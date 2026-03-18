from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.user import UserRole


class PromotionRule(Base):
    """A rule that defines: if a user has certificates for all required courses → promote to target_role."""

    __tablename__ = "promotion_rules"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    target_role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))

    requirements = relationship("PromotionRuleRequirement", back_populates="rule", cascade="all, delete-orphan")


class PromotionRuleRequirement(Base):
    """A single required course certificate for a promotion rule."""

    __tablename__ = "promotion_rule_requirements"
    __table_args__ = (UniqueConstraint("rule_id", "course_id", name="uq_rule_course"),)

    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("promotion_rules.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)

    rule = relationship("PromotionRule", back_populates="requirements")
    course = relationship("Course")


class PromotionLog(Base):
    """Records when a user was automatically promoted by a rule."""

    __tablename__ = "promotion_log"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rule_id = Column(Integer, ForeignKey("promotion_rules.id"), nullable=False)
    previous_role = Column(Enum(UserRole), nullable=False)
    new_role = Column(Enum(UserRole), nullable=False)
    promoted_at = Column(DateTime, default=lambda: datetime.now(UTC))

    user = relationship("User")
    rule = relationship("PromotionRule")
