"""Tests for Discord role sync and profile update (discord_id)."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.promotion import PromotionRule, PromotionRuleRequirement
from app.models.user import User, UserRole
from app.services.discord_bot import _get_role_map, sync_discord_role

SQLALCHEMY_TEST_URL = "sqlite:///./test_discord_sync.db"
engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def student(db_session):
    user = User(github_id=55555, username="syncstudent", email="s@test.com", role=UserRole.student)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student_with_discord(db_session):
    user = User(
        github_id=55556,
        username="discordstudent",
        email="ds@test.com",
        role=UserRole.student,
        discord_id="123456789012345678",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin(db_session):
    user = User(github_id=66666, username="syncadmin", email="a@test.com", role=UserRole.admin)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _auth_header(user):
    from app.auth.jwt import create_access_token

    token = create_access_token(user.id)
    return {"Authorization": f"Bearer {token}"}


# --- sync_discord_role unit tests ---


class TestSyncDiscordRole:
    @patch("app.services.discord_bot.settings")
    def test_not_configured_returns_false(self, mock_settings):
        mock_settings.discord_bot_token = ""
        mock_settings.discord_guild_id = ""
        mock_settings.discord_role_map = ""
        assert sync_discord_role("123456789012345678", "mentor") is False

    @patch("app.services.discord_bot.settings")
    def test_no_discord_id_returns_false(self, mock_settings):
        mock_settings.discord_bot_token = "token"
        mock_settings.discord_guild_id = "guild"
        mock_settings.discord_role_map = "student:111,mentor:222"
        assert sync_discord_role("", "mentor") is False

    @patch("app.services.discord_bot.httpx.put")
    @patch("app.services.discord_bot.settings")
    def test_adds_new_role(self, mock_settings, mock_put):
        mock_settings.discord_bot_token = "token"
        mock_settings.discord_guild_id = "guild123"
        mock_settings.discord_role_map = "student:111,mentor:222,admin:333"
        mock_put.return_value = MagicMock(status_code=204)

        result = sync_discord_role("123456789012345678", "mentor")
        assert result is True
        mock_put.assert_called_once()
        assert "/roles/222" in mock_put.call_args[0][0]

    @patch("app.services.discord_bot.httpx.delete")
    @patch("app.services.discord_bot.httpx.put")
    @patch("app.services.discord_bot.settings")
    def test_removes_old_adds_new(self, mock_settings, mock_put, mock_delete):
        mock_settings.discord_bot_token = "token"
        mock_settings.discord_guild_id = "guild123"
        mock_settings.discord_role_map = "student:111,mentor:222,admin:333"
        mock_put.return_value = MagicMock(status_code=204)
        mock_delete.return_value = MagicMock(status_code=204)

        result = sync_discord_role("123456789012345678", "mentor", "student")
        assert result is True
        mock_delete.assert_called_once()
        assert "/roles/111" in mock_delete.call_args[0][0]
        mock_put.assert_called_once()
        assert "/roles/222" in mock_put.call_args[0][0]

    @patch("app.services.discord_bot.httpx.put")
    @patch("app.services.discord_bot.settings")
    def test_unmapped_role_returns_false(self, mock_settings, mock_put):
        mock_settings.discord_bot_token = "token"
        mock_settings.discord_guild_id = "guild123"
        mock_settings.discord_role_map = "student:111"
        result = sync_discord_role("123456789012345678", "mentor")
        assert result is False
        mock_put.assert_not_called()

    @patch("app.services.discord_bot.httpx.put")
    @patch("app.services.discord_bot.settings")
    def test_api_failure_returns_false(self, mock_settings, mock_put):
        mock_settings.discord_bot_token = "token"
        mock_settings.discord_guild_id = "guild123"
        mock_settings.discord_role_map = "student:111,mentor:222"
        mock_put.return_value = MagicMock(status_code=403, text="Missing Permissions")

        result = sync_discord_role("123456789012345678", "mentor")
        assert result is False


# --- GET/PATCH /api/auth/me tests ---


class TestProfileDiscordId:
    def test_me_returns_discord_id(self, client, student):
        r = client.get("/api/auth/me", headers=_auth_header(student))
        assert r.status_code == 200
        assert r.json()["discord_id"] is None

    def test_me_returns_discord_id_when_set(self, client, student_with_discord):
        r = client.get("/api/auth/me", headers=_auth_header(student_with_discord))
        assert r.status_code == 200
        assert r.json()["discord_id"] == "123456789012345678"

    @patch("app.routers.auth.lookup_discord_member", return_value={"user": {"id": "123456789012345678"}})
    @patch("app.routers.auth.sync_discord_role", return_value=True)
    def test_set_discord_id(self, mock_sync, mock_lookup, client, student):
        r = client.patch(
            "/api/auth/me",
            json={"discord_id": "123456789012345678"},
            headers=_auth_header(student),
        )
        assert r.status_code == 200
        assert r.json()["discord_id"] == "123456789012345678"
        mock_sync.assert_called_once_with("123456789012345678", "student")

    @patch("app.routers.auth.lookup_discord_member", return_value={"user": {"id": "123456789012345678"}})
    @patch("app.routers.auth.sync_discord_role", return_value=True)
    def test_clear_discord_id(self, mock_sync, mock_lookup, client, student_with_discord):
        r = client.patch(
            "/api/auth/me",
            json={"discord_id": ""},
            headers=_auth_header(student_with_discord),
        )
        assert r.status_code == 200
        assert r.json()["discord_id"] is None

    def test_invalid_discord_id_format(self, client, student):
        r = client.patch(
            "/api/auth/me",
            json={"discord_id": "not-a-number"},
            headers=_auth_header(student),
        )
        assert r.status_code == 400
        assert "numeric" in r.json()["detail"].lower() or "Invalid" in r.json()["detail"]

    def test_discord_id_too_short(self, client, student):
        r = client.patch(
            "/api/auth/me",
            json={"discord_id": "12345"},
            headers=_auth_header(student),
        )
        assert r.status_code == 400

    @patch("app.routers.auth.lookup_discord_member", return_value={"user": {"id": "999888777666555444"}})
    @patch("app.routers.auth.sync_discord_role", return_value=True)
    def test_duplicate_discord_id_rejected(self, mock_sync, mock_lookup, client, student, student_with_discord):
        r = client.patch(
            "/api/auth/me",
            json={"discord_id": "123456789012345678"},  # already used by student_with_discord
            headers=_auth_header(student),
        )
        assert r.status_code == 409

    @patch("app.routers.auth.lookup_discord_member", return_value=None)
    @patch("app.routers.auth.settings")
    def test_discord_member_not_found(self, mock_settings, mock_lookup, client, student):
        mock_settings.discord_bot_token = "token"
        mock_settings.discord_guild_id = "guild"
        r = client.patch(
            "/api/auth/me",
            json={"discord_id": "999888777666555444"},
            headers=_auth_header(student),
        )
        assert r.status_code == 400
        assert "not found" in r.json()["detail"].lower()


# --- Admin role change triggers Discord sync ---


class TestAdminRoleChangeSync:
    @patch("app.services.discord_bot.sync_discord_role", return_value=True)
    def test_admin_role_change_syncs_discord(self, mock_sync, client, admin, student_with_discord):
        r = client.patch(
            f"/api/admin/users/{student_with_discord.id}/role",
            json={"role": "mentor"},
            headers=_auth_header(admin),
        )
        assert r.status_code == 200
        assert r.json()["role"] == "mentor"
        mock_sync.assert_called_once_with("123456789012345678", "mentor", "student")

    @patch("app.services.discord_bot.sync_discord_role")
    def test_admin_role_change_no_discord_no_sync(self, mock_sync, client, admin, student):
        """No discord_id → sync_discord_role should not be called."""
        r = client.patch(
            f"/api/admin/users/{student.id}/role",
            json={"role": "mentor"},
            headers=_auth_header(admin),
        )
        assert r.status_code == 200
        mock_sync.assert_not_called()


# --- Promotion triggers Discord sync ---


class TestPromotionDiscordSync:
    @patch("app.services.promotion.sync_discord_role", return_value=True)
    @patch("app.services.promotion.notify_promotion", return_value=True)
    def test_promotion_syncs_discord(self, mock_notify, mock_sync, db_session):
        from app.services.promotion import check_and_promote

        course = Course(name="Test", description="")
        db_session.add(course)
        db_session.commit()
        db_session.refresh(course)

        user = User(
            github_id=77777,
            username="promostudent",
            email="p@test.com",
            role=UserRole.student,
            discord_id="111222333444555666",
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        cert = Certificate(user_id=user.id, course_id=course.id, cert_id="test-cert-uuid")
        db_session.add(cert)
        db_session.commit()

        rule = PromotionRule(name="Test Promo", target_role=UserRole.mentor, is_active=True)
        db_session.add(rule)
        db_session.commit()
        db_session.refresh(rule)

        req = PromotionRuleRequirement(rule_id=rule.id, course_id=course.id)
        db_session.add(req)
        db_session.commit()

        log = check_and_promote(db_session, user)
        assert log is not None
        assert log.new_role == UserRole.mentor
        mock_sync.assert_called_once_with("111222333444555666", "mentor", "student")


# --- _get_role_map parsing ---


class TestGetRoleMap:
    @patch("app.services.discord_bot.settings")
    def test_parses_role_map(self, mock_settings):
        mock_settings.discord_role_map = "student:111,mentor:222,admin:333"
        result = _get_role_map()
        assert result == {"student": "111", "mentor": "222", "admin": "333"}

    @patch("app.services.discord_bot.settings")
    def test_empty_role_map(self, mock_settings):
        mock_settings.discord_role_map = ""
        assert _get_role_map() == {}

    @patch("app.services.discord_bot.settings")
    def test_handles_spaces(self, mock_settings):
        mock_settings.discord_role_map = " student : 111 , mentor : 222 "
        result = _get_role_map()
        assert result == {"student": "111", "mentor": "222"}
