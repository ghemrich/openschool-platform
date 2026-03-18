import enum
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String

from app.database import Base


class UserRole(enum.StrEnum):
    student = "student"
    mentor = "mentor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    github_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    email = Column(String)
    avatar_url = Column(String)
    role = Column(Enum(UserRole), default=UserRole.student, nullable=False)
    discord_id = Column(String, unique=True, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    last_login = Column(DateTime)
