from datetime import UTC, datetime

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.jwt import ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token, create_refresh_token
from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.discord_bot import lookup_discord_member, sync_discord_role
from app.services.github import invite_user_to_org

router = APIRouter(prefix="/api/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"


@router.get("/login")
@limiter.limit("10/minute")
def auth_login(request: Request, response: Response):
    """Redirect to GitHub OAuth authorization page."""
    import secrets

    state = secrets.token_urlsafe(32)
    scope = "read:user%20user:email"
    url = f"{GITHUB_AUTHORIZE_URL}?client_id={settings.github_client_id}&scope={scope}&state={state}"
    resp = RedirectResponse(url=url)
    resp.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        max_age=600,
        secure=settings.environment != "development",
    )
    return resp


@router.get("/callback")
@limiter.limit("10/minute")
def auth_callback(
    code: str,
    state: str = "",
    request: Request = None,
    db: Session = Depends(get_db),
    response: Response = None,
):
    """Handle GitHub OAuth callback: exchange code for token, create/update user, return JWT."""
    # Verify OAuth state to prevent CSRF
    expected_state = request.cookies.get("oauth_state") if request else None
    if not expected_state or not state or expected_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state")

    # Exchange code for access token
    token_response = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": settings.github_client_id,
            "client_secret": settings.github_client_secret,
            "code": code,
        },
        headers={"Accept": "application/json"},
    )
    token_data = token_response.json()

    if "access_token" not in token_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub OAuth failed")

    # Get user info from GitHub
    user_response = httpx.get(
        GITHUB_USER_URL,
        headers={"Authorization": f"Bearer {token_data['access_token']}"},
    )
    github_user = user_response.json()

    if "id" not in github_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to get GitHub user info")

    # Create or update user
    user = db.query(User).filter(User.github_id == github_user["id"]).first()
    if user:
        user.last_login = datetime.now(UTC)
        user.username = github_user.get("login", user.username)
        user.avatar_url = github_user.get("avatar_url", user.avatar_url)
        user.email = github_user.get("email", user.email)
    else:
        user = User(
            github_id=github_user["id"],
            username=github_user.get("login", ""),
            email=github_user.get("email"),
            avatar_url=github_user.get("avatar_url"),
            last_login=datetime.now(UTC),
        )
        db.add(user)

    db.commit()
    db.refresh(user)

    # Auto-invite user to GitHub org (if configured)
    if settings.github_org and settings.github_org_admin_token:
        invite_user_to_org(user.username, settings.github_org, settings.github_org_admin_token)

    # Generate tokens
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Set tokens as secure HTTP-only cookies
    resp = RedirectResponse(url="/dashboard", status_code=302)
    is_secure = settings.environment != "development"
    resp.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=is_secure,
        path="/",
    )
    resp.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        secure=is_secure,
        path="/",
    )
    resp.delete_cookie(key="oauth_state")
    return resp


@router.get("/me")
def auth_me(current_user: User = Depends(get_current_user)):
    """Return current authenticated user info."""
    return {
        "id": current_user.id,
        "github_id": current_user.github_id,
        "username": current_user.username,
        "email": current_user.email,
        "avatar_url": current_user.avatar_url,
        "role": current_user.role.value,
        "discord_id": current_user.discord_id,
    }


class ProfileUpdate(BaseModel):
    discord_id: str | None = None


@router.patch("/me")
def update_profile(
    data: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update current user's profile (discord_id)."""
    if data.discord_id is not None:
        # Allow clearing by setting to empty string
        if data.discord_id == "":
            current_user.discord_id = None
            db.commit()
            return {"discord_id": None}

        # Validate: must be a numeric Discord user ID (snowflake)
        discord_id = data.discord_id.strip()
        if not discord_id.isdigit() or len(discord_id) < 17 or len(discord_id) > 20:
            raise HTTPException(status_code=400, detail="Invalid Discord ID — use your numeric user ID (17-20 digits)")

        # Check uniqueness
        existing = db.query(User).filter(User.discord_id == discord_id, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="This Discord ID is already linked to another account")

        # Verify the user exists on the Discord server
        member = lookup_discord_member(discord_id)
        if member is None and settings.discord_bot_token and settings.discord_guild_id:
            raise HTTPException(status_code=400, detail="Discord user not found on the server — join first")

        current_user.discord_id = discord_id
        db.commit()

        # Sync current role to Discord
        sync_discord_role(discord_id, current_user.role.value)

        return {"discord_id": discord_id}

    return {"discord_id": current_user.discord_id}


@router.post("/refresh")
@limiter.limit("20/minute")
def auth_refresh(request: Request, db: Session = Depends(get_db)):
    """Issue new access and refresh tokens using the refresh token cookie (rotation)."""
    from app.auth.jwt import REFRESH_TOKEN_EXPIRE_DAYS, verify_token

    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        token_data = verify_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from None

    if token_data.get("payload", {}).get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    user = db.query(User).filter(User.id == token_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Rotate: issue both new access and new refresh tokens
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)

    resp = Response(content='{"access_token": "ok", "token_type": "bearer"}')
    resp.headers["Content-Type"] = "application/json"
    is_secure = settings.environment != "development"
    resp.set_cookie(
        key="access_token",
        value=new_access_token,
        httponly=True,
        samesite="lax",
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=is_secure,
        path="/",
    )
    resp.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        secure=is_secure,
        path="/",
    )
    return resp


@router.post("/logout")
def auth_logout(response: Response):
    """Clear auth cookies."""
    response = Response(content='{"detail": "Logged out"}')
    response.headers["Content-Type"] = "application/json"
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return response
