import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.database import engine  # noqa: F401
from app.models.certificate import Certificate  # noqa: F401
from app.models.course import Course, Enrollment, Exercise, Module, Progress  # noqa: F401
from app.models.promotion import PromotionLog, PromotionRule, PromotionRuleRequirement  # noqa: F401
from app.routers import admin, auth, certificates, courses, dashboard, webhooks

logging.basicConfig(
    level=logging.INFO if settings.environment == "production" else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_real_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For header when behind a reverse proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


limiter = Limiter(key_func=_get_real_ip)

app = FastAPI(
    title="OpenSchool API",
    docs_url=None if settings.environment in ("production", "staging") else "/docs",
    redoc_url=None if settings.environment in ("production", "staging") else "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(auth.router)
app.include_router(courses.router)
app.include_router(dashboard.router)
app.include_router(certificates.router)
app.include_router(webhooks.router)
app.include_router(admin.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
