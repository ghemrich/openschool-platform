from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.dependencies import require_role
from app.database import get_db
from app.models.certificate import Certificate
from app.models.course import Course, Enrollment, Exercise, Module, Progress
from app.models.user import User, UserRole

router = APIRouter(prefix="/api/admin", tags=["admin"])


# --- Schemas ---


class RoleUpdate(BaseModel):
    role: str


# --- Dashboard / Stats ---


@router.get("/stats")
def admin_stats(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Overview statistics for admin dashboard."""
    return {
        "users": db.query(User).count(),
        "courses": db.query(Course).count(),
        "enrollments": db.query(Enrollment).count(),
        "certificates": db.query(Certificate).count(),
        "exercises": db.query(Exercise).count(),
    }


# --- User management ---


@router.get("/users")
def list_users(
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """List all users."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "avatar_url": u.avatar_url,
            "role": u.role.value if u.role else "student",
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_login": u.last_login.isoformat() if u.last_login else None,
        }
        for u in users
    ]


@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    data: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_role(UserRole.admin)),
):
    """Change a user's role."""
    if data.role not in ("student", "mentor", "admin"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    user.role = UserRole(data.role)
    db.commit()
    return {"id": user.id, "username": user.username, "role": user.role.value}


# --- Course management ---


@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete a course and all its modules, exercises, enrollments, progress."""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    modules = db.query(Module).filter(Module.course_id == course_id).all()
    module_ids = [m.id for m in modules]

    if module_ids:
        exercise_ids = [e.id for e in db.query(Exercise.id).filter(Exercise.module_id.in_(module_ids)).all()]
        if exercise_ids:
            db.query(Progress).filter(Progress.exercise_id.in_(exercise_ids)).delete(synchronize_session=False)
        db.query(Exercise).filter(Exercise.module_id.in_(module_ids)).delete(synchronize_session=False)

    db.query(Module).filter(Module.course_id == course_id).delete(synchronize_session=False)
    db.query(Enrollment).filter(Enrollment.course_id == course_id).delete(synchronize_session=False)
    db.query(Certificate).filter(Certificate.course_id == course_id).delete(synchronize_session=False)
    db.delete(course)
    db.commit()
    return {"detail": "Course deleted"}


@router.delete("/modules/{module_id}")
def delete_module(
    module_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete a module and its exercises."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(status_code=404, detail="Module not found")

    exercise_ids = [e.id for e in db.query(Exercise.id).filter(Exercise.module_id == module_id).all()]
    if exercise_ids:
        db.query(Progress).filter(Progress.exercise_id.in_(exercise_ids)).delete(synchronize_session=False)
    db.query(Exercise).filter(Exercise.module_id == module_id).delete(synchronize_session=False)
    db.delete(module)
    db.commit()
    return {"detail": "Module deleted"}


@router.delete("/exercises/{exercise_id}")
def delete_exercise(
    exercise_id: int,
    db: Session = Depends(get_db),
    _admin: User = Depends(require_role(UserRole.admin)),
):
    """Delete an exercise and its progress records."""
    exercise = db.query(Exercise).filter(Exercise.id == exercise_id).first()
    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")

    db.query(Progress).filter(Progress.exercise_id == exercise_id).delete(synchronize_session=False)
    db.delete(exercise)
    db.commit()
    return {"detail": "Exercise deleted"}
