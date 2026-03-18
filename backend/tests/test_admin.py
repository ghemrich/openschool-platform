import pytest

from app.auth.jwt import create_access_token
from app.models.course import Course, Exercise, Module
from app.models.promotion import PromotionRule, PromotionRuleRequirement
from app.models.user import User, UserRole


@pytest.fixture
def admin(db_session):
    user = User(github_id=1000, username="adminuser", email="admin@test.com", role=UserRole.admin)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def student(db_session):
    user = User(github_id=2000, username="studentuser", email="student@test.com", role=UserRole.student)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def mentor(db_session):
    user = User(github_id=3000, username="mentoruser", email="mentor@test.com", role=UserRole.mentor)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# --- Stats ---


def test_stats_requires_admin(client, student):
    token = create_access_token(student.id)
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_stats_returns_counts(client, admin, db_session):
    course = Course(name="Test Course")
    db_session.add(course)
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.get("/api/admin/stats", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["users"] >= 1
    assert data["courses"] == 1
    assert "enrollments" in data
    assert "certificates" in data
    assert "exercises" in data


# --- User management ---


def test_list_users(client, admin, student, mentor):
    token = create_access_token(admin.id)
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 3
    users = body["data"]
    assert len(users) == 3
    usernames = [u["username"] for u in users]
    assert "adminuser" in usernames
    assert "studentuser" in usernames
    assert "mentoruser" in usernames


def test_list_users_forbidden_for_student(client, student):
    token = create_access_token(student.id)
    response = client.get("/api/admin/users", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


def test_update_user_role(client, admin, student):
    token = create_access_token(admin.id)
    response = client.patch(
        f"/api/admin/users/{student.id}/role",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"role": "mentor"},
    )
    assert response.status_code == 200
    assert response.json()["role"] == "mentor"


def test_update_own_role_forbidden(client, admin):
    token = create_access_token(admin.id)
    response = client.patch(
        f"/api/admin/users/{admin.id}/role",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"role": "student"},
    )
    assert response.status_code == 400


def test_update_role_invalid(client, admin, student):
    token = create_access_token(admin.id)
    response = client.patch(
        f"/api/admin/users/{student.id}/role",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"role": "superadmin"},
    )
    assert response.status_code == 400


# --- Delete course ---


def test_delete_course(client, admin, db_session):
    course = Course(name="To Delete")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    module = Module(course_id=course.id, name="Mod 1", order=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    exercise = Exercise(module_id=module.id, name="Ex 1", order=1)
    db_session.add(exercise)
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.delete(f"/api/admin/courses/{course.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    assert db_session.query(Course).filter(Course.id == course.id).first() is None
    assert db_session.query(Module).filter(Module.course_id == course.id).first() is None


def test_delete_course_forbidden_for_student(client, student, db_session):
    course = Course(name="Protected")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    token = create_access_token(student.id)
    response = client.delete(f"/api/admin/courses/{course.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403


# --- Delete module ---


def test_delete_module(client, admin, db_session):
    course = Course(name="C")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    module = Module(course_id=course.id, name="M", order=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    token = create_access_token(admin.id)
    response = client.delete(f"/api/admin/modules/{module.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert db_session.query(Module).filter(Module.id == module.id).first() is None


# --- Delete exercise ---


def test_delete_exercise(client, admin, db_session):
    course = Course(name="C")
    db_session.add(course)
    db_session.commit()
    db_session.refresh(course)

    module = Module(course_id=course.id, name="M", order=1)
    db_session.add(module)
    db_session.commit()
    db_session.refresh(module)

    exercise = Exercise(module_id=module.id, name="E", order=1)
    db_session.add(exercise)
    db_session.commit()
    db_session.refresh(exercise)

    token = create_access_token(admin.id)
    response = client.delete(f"/api/admin/exercises/{exercise.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert db_session.query(Exercise).filter(Exercise.id == exercise.id).first() is None


# --- Promotion rules ---


def test_list_promotion_rules_empty(client, admin):
    token = create_access_token(admin.id)
    response = client.get("/api/admin/promotion-rules", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json() == []


def test_create_promotion_rule(client, admin, db_session):
    c1 = Course(name="Course A")
    c2 = Course(name="Course B")
    db_session.add_all([c1, c2])
    db_session.commit()
    db_session.refresh(c1)
    db_session.refresh(c2)

    token = create_access_token(admin.id)
    response = client.post(
        "/api/admin/promotion-rules",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "All → Mentor",
            "description": "Complete all courses",
            "target_role": "mentor",
            "course_ids": [c1.id, c2.id],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "All → Mentor"
    assert data["target_role"] == "mentor"
    assert data["is_active"] is True
    assert set(data["course_ids"]) == {c1.id, c2.id}


def test_create_promotion_rule_invalid_role(client, admin, db_session):
    c = Course(name="C")
    db_session.add(c)
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.post(
        "/api/admin/promotion-rules",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Bad", "target_role": "superadmin", "course_ids": [c.id]},
    )
    assert response.status_code == 400


def test_create_promotion_rule_missing_courses(client, admin):
    token = create_access_token(admin.id)
    response = client.post(
        "/api/admin/promotion-rules",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Empty", "target_role": "mentor", "course_ids": []},
    )
    assert response.status_code == 400


def test_create_promotion_rule_nonexistent_course(client, admin):
    token = create_access_token(admin.id)
    response = client.post(
        "/api/admin/promotion-rules",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Bad", "target_role": "mentor", "course_ids": [9999]},
    )
    assert response.status_code == 400


def test_get_single_promotion_rule(client, admin, db_session):
    c = Course(name="C")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)

    rule = PromotionRule(name="Test", target_role=UserRole.mentor)
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c.id))
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.get(f"/api/admin/promotion-rules/{rule.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_update_promotion_rule(client, admin, db_session):
    c = Course(name="C")
    db_session.add(c)
    db_session.commit()
    db_session.refresh(c)

    rule = PromotionRule(name="Old", target_role=UserRole.mentor)
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)
    db_session.add(PromotionRuleRequirement(rule_id=rule.id, course_id=c.id))
    db_session.commit()

    token = create_access_token(admin.id)
    response = client.patch(
        f"/api/admin/promotion-rules/{rule.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Updated", "is_active": False},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"
    assert response.json()["is_active"] is False


def test_delete_promotion_rule(client, admin, db_session):
    rule = PromotionRule(name="ToDelete", target_role=UserRole.mentor)
    db_session.add(rule)
    db_session.commit()
    db_session.refresh(rule)

    token = create_access_token(admin.id)
    response = client.delete(f"/api/admin/promotion-rules/{rule.id}", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert db_session.query(PromotionRule).filter(PromotionRule.id == rule.id).first() is None


def test_promotion_rules_forbidden_for_student(client, student):
    token = create_access_token(student.id)
    response = client.get("/api/admin/promotion-rules", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
