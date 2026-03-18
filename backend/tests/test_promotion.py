from unittest.mock import patch

import pytest

from app.auth.jwt import create_access_token
from app.models.certificate import Certificate
from app.models.course import Course
from app.models.promotion import PromotionRule, PromotionRuleRequirement
from app.models.user import User, UserRole
from app.services.promotion import check_and_promote

# --- Fixtures ---


@pytest.fixture
def admin(db_session):
    user = User(github_id=9000, username="promo_admin", email="pa@test.com", role=UserRole.admin)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student(db_session):
    user = User(github_id=9001, username="promo_student", email="ps@test.com", role=UserRole.student)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def courses(db_session):
    c1 = Course(name="Python Haladó")
    c2 = Course(name="Mentor Képzés")
    db_session.add_all([c1, c2])
    db_session.commit()
    db_session.refresh(c1)
    db_session.refresh(c2)
    return c1, c2


@pytest.fixture
def mentor_rule(db_session, courses):
    c1, c2 = courses
    rule = PromotionRule(name="Mentor előléptetés", target_role=UserRole.mentor)
    db_session.add(rule)
    db_session.flush()
    db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c1.id))
    db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c2.id))
    db_session.commit()
    db_session.refresh(rule)
    return rule


# --- Promotion service tests ---


class TestCheckAndPromote:
    @patch("app.services.promotion.notify_promotion")
    def test_no_rules_returns_none(self, mock_notify, db_session, student):
        result = check_and_promote(db_session, student)
        assert result is None
        mock_notify.assert_not_called()

    @patch("app.services.promotion.notify_promotion")
    def test_missing_certificate_returns_none(self, mock_notify, db_session, student, courses, mentor_rule):
        # Student has only one of the two required certificates.
        c1, _ = courses
        db_session.add(Certificate(user_id=student.id, course_id=c1.id))
        db_session.commit()

        result = check_and_promote(db_session, student)
        assert result is None
        assert student.role == UserRole.student

    @patch("app.services.promotion.notify_promotion")
    def test_all_certificates_triggers_promotion(self, mock_notify, db_session, student, courses, mentor_rule):
        c1, c2 = courses
        db_session.add(Certificate(user_id=student.id, course_id=c1.id))
        db_session.add(Certificate(user_id=student.id, course_id=c2.id))
        db_session.commit()

        result = check_and_promote(db_session, student)
        assert result is not None
        assert result.new_role == UserRole.mentor
        assert result.previous_role == UserRole.student
        assert student.role == UserRole.mentor
        mock_notify.assert_called_once_with("promo_student", "mentor", "Mentor előléptetés")

    @patch("app.services.promotion.notify_promotion")
    def test_already_promoted_user_skipped(self, mock_notify, db_session, student, courses, mentor_rule):
        c1, c2 = courses
        db_session.add(Certificate(user_id=student.id, course_id=c1.id))
        db_session.add(Certificate(user_id=student.id, course_id=c2.id))
        db_session.commit()

        # Promote first time.
        check_and_promote(db_session, student)
        mock_notify.reset_mock()

        # Second call should not promote again.
        result = check_and_promote(db_session, student)
        assert result is None
        mock_notify.assert_not_called()

    @patch("app.services.promotion.notify_promotion")
    def test_inactive_rule_skipped(self, mock_notify, db_session, student, courses, mentor_rule):
        c1, c2 = courses
        mentor_rule.is_active = False
        db_session.commit()
        db_session.add(Certificate(user_id=student.id, course_id=c1.id))
        db_session.add(Certificate(user_id=student.id, course_id=c2.id))
        db_session.commit()

        result = check_and_promote(db_session, student)
        assert result is None
        assert student.role == UserRole.student

    @patch("app.services.promotion.notify_promotion")
    def test_mentor_not_demoted_to_student(self, mock_notify, db_session, courses):
        """A rule targeting 'student' should not demote a mentor."""
        c1, _ = courses
        mentor = User(github_id=9099, username="already_mentor", role=UserRole.mentor)
        db_session.add(mentor)
        db_session.commit()
        db_session.refresh(mentor)

        rule = PromotionRule(name="Student rule", target_role=UserRole.student)
        db_session.add(rule)
        db_session.flush()
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c1.id))
        db_session.add(Certificate(user_id=mentor.id, course_id=c1.id))
        db_session.commit()

        result = check_and_promote(db_session, mentor)
        assert result is None
        assert mentor.role == UserRole.mentor


# --- Admin promotion rule CRUD tests ---


class TestAdminPromotionRules:
    def test_list_rules_empty(self, client, admin):
        token = create_access_token(admin.id)
        resp = client.get("/api/admin/promotion-rules", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json() == []

    def test_create_rule(self, client, admin, db_session):
        c1 = Course(name="Course A")
        c2 = Course(name="Course B")
        db_session.add_all([c1, c2])
        db_session.commit()

        token = create_access_token(admin.id)
        resp = client.post(
            "/api/admin/promotion-rules",
            json={
                "name": "Mentor Rule",
                "target_role": "mentor",
                "course_ids": [c1.id, c2.id],
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Mentor Rule"
        assert data["target_role"] == "mentor"
        assert sorted(data["course_ids"]) == sorted([c1.id, c2.id])
        assert data["is_active"] is True

    def test_create_rule_invalid_role(self, client, admin, db_session):
        c = Course(name="C")
        db_session.add(c)
        db_session.commit()

        token = create_access_token(admin.id)
        resp = client.post(
            "/api/admin/promotion-rules",
            json={"name": "Bad", "target_role": "superadmin", "course_ids": [c.id]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_create_rule_missing_courses(self, client, admin):
        token = create_access_token(admin.id)
        resp = client.post(
            "/api/admin/promotion-rules",
            json={"name": "Bad", "target_role": "mentor", "course_ids": [9999]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400
        assert "9999" in resp.json()["detail"]

    def test_create_rule_empty_courses(self, client, admin):
        token = create_access_token(admin.id)
        resp = client.post(
            "/api/admin/promotion-rules",
            json={"name": "Bad", "target_role": "mentor", "course_ids": []},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400

    def test_get_rule(self, client, admin, db_session):
        c = Course(name="Get Test")
        db_session.add(c)
        db_session.commit()
        rule = PromotionRule(name="R1", target_role=UserRole.mentor)
        db_session.add(rule)
        db_session.flush()
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c.id))
        db_session.commit()

        token = create_access_token(admin.id)
        resp = client.get(f"/api/admin/promotion-rules/{rule.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["name"] == "R1"

    def test_get_rule_not_found(self, client, admin):
        token = create_access_token(admin.id)
        resp = client.get("/api/admin/promotion-rules/999", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 404

    def test_update_rule(self, client, admin, db_session):
        c1 = Course(name="Upd A")
        c2 = Course(name="Upd B")
        db_session.add_all([c1, c2])
        db_session.commit()
        rule = PromotionRule(name="Old", target_role=UserRole.mentor)
        db_session.add(rule)
        db_session.flush()
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c1.id))
        db_session.commit()

        token = create_access_token(admin.id)
        resp = client.patch(
            f"/api/admin/promotion-rules/{rule.id}",
            json={"name": "New", "course_ids": [c2.id]},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "New"
        assert data["course_ids"] == [c2.id]

    def test_update_rule_deactivate(self, client, admin, db_session):
        c = Course(name="Deact")
        db_session.add(c)
        db_session.commit()
        rule = PromotionRule(name="Active", target_role=UserRole.mentor)
        db_session.add(rule)
        db_session.flush()
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c.id))
        db_session.commit()

        token = create_access_token(admin.id)
        resp = client.patch(
            f"/api/admin/promotion-rules/{rule.id}",
            json={"is_active": False},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

    def test_delete_rule(self, client, admin, db_session):
        c = Course(name="Del")
        db_session.add(c)
        db_session.commit()
        rule = PromotionRule(name="ToDelete", target_role=UserRole.mentor)
        db_session.add(rule)
        db_session.flush()
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c.id))
        db_session.commit()

        token = create_access_token(admin.id)
        resp = client.delete(f"/api/admin/promotion-rules/{rule.id}", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["detail"] == "Promotion rule deleted"

        # Verify cascaded delete of requirements.
        assert db_session.query(PromotionRuleRequirement).filter_by(rule_id=rule.id).count() == 0

    def test_requires_admin(self, client, db_session):
        student = User(github_id=9002, username="not_admin", role=UserRole.student)
        db_session.add(student)
        db_session.commit()
        token = create_access_token(student.id)
        resp = client.get("/api/admin/promotion-rules", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403


class TestAdminPromotionLog:
    def test_promotion_log(self, client, admin, db_session, student, courses, mentor_rule):
        c1, c2 = courses
        db_session.add(Certificate(user_id=student.id, course_id=c1.id))
        db_session.add(Certificate(user_id=student.id, course_id=c2.id))
        db_session.commit()

        with patch("app.services.promotion.notify_promotion"):
            check_and_promote(db_session, student)

        token = create_access_token(admin.id)
        resp = client.get("/api/admin/promotion-log", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["new_role"] == "mentor"
        assert data["data"][0]["previous_role"] == "student"


# --- Integration: certificate triggers promotion ---


class TestCertificatePromotion:
    def test_certificate_triggers_promotion(self, client, db_session, tmp_path):
        """Requesting a certificate that completes a promotion rule should promote the user."""
        from app.models.course import Enrollment, Exercise, Module, Progress, ProgressStatus

        student = User(github_id=9500, username="cert_promo", role=UserRole.student)
        db_session.add(student)
        db_session.commit()
        db_session.refresh(student)

        # Create two courses, each with one required exercise.
        c1 = Course(name="Course 1")
        c2 = Course(name="Course 2")
        db_session.add_all([c1, c2])
        db_session.commit()

        m1 = Module(course_id=c1.id, name="M1")
        m2 = Module(course_id=c2.id, name="M2")
        db_session.add_all([m1, m2])
        db_session.commit()

        e1 = Exercise(module_id=m1.id, name="E1", required=True)
        e2 = Exercise(module_id=m2.id, name="E2", required=True)
        db_session.add_all([e1, e2])
        db_session.commit()

        # Enroll and complete both.
        db_session.add(Enrollment(user_id=student.id, course_id=c1.id))
        db_session.add(Enrollment(user_id=student.id, course_id=c2.id))
        db_session.add(Progress(user_id=student.id, exercise_id=e1.id, status=ProgressStatus.completed))
        db_session.add(Progress(user_id=student.id, exercise_id=e2.id, status=ProgressStatus.completed))
        db_session.commit()

        # Give student a certificate for course 1 already.
        db_session.add(Certificate(user_id=student.id, course_id=c1.id))
        db_session.commit()

        # Create a promotion rule: c1 + c2 → mentor.
        rule = PromotionRule(name="Mentor Rule", target_role=UserRole.mentor)
        db_session.add(rule)
        db_session.flush()
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c1.id))
        db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c2.id))
        db_session.commit()

        # Request certificate for course 2 — should trigger promotion.
        token = create_access_token(student.id)
        with (
            patch("app.services.pdf.generate_certificate_pdf", return_value=b"%PDF-fake"),
            patch("app.services.qr.generate_qr_base64", return_value="fakebase64"),
            patch("app.routers.certificates.CERT_DIR", tmp_path),
            patch("app.routers.certificates.notify_certificate"),
            patch("app.services.promotion.notify_promotion"),
        ):
            resp = client.post(
                f"/api/me/courses/{c2.id}/certificate",
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data.get("promoted_to") == "mentor"

        # Verify user was promoted in DB.
        db_session.refresh(student)
        assert student.role == UserRole.mentor
