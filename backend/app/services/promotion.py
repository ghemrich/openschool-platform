import logging

from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.promotion import PromotionLog, PromotionRule, PromotionRuleRequirement
from app.models.user import User, UserRole
from app.services.discord import notify_promotion
from app.services.discord_bot import sync_discord_role

logger = logging.getLogger(__name__)

# Define a role hierarchy so we only promote upward.
_ROLE_RANK = {UserRole.student: 0, UserRole.mentor: 1, UserRole.admin: 2}


def check_and_promote(db: Session, user: User) -> PromotionLog | None:
    """Check all active promotion rules and promote the user if any rule is fully satisfied.

    Returns the PromotionLog entry if promoted, or None.
    """
    rules = db.query(PromotionRule).filter(PromotionRule.is_active.is_(True)).all()
    if not rules:
        return None

    # Gather courses the user already has certificates for.
    user_cert_course_ids = {
        row[0] for row in db.query(Certificate.course_id).filter(Certificate.user_id == user.id).all()
    }

    for rule in rules:
        # Skip if the user already has this role or higher.
        if _ROLE_RANK.get(user.role, 0) >= _ROLE_RANK.get(rule.target_role, 0):
            continue

        # Skip if user was already promoted by this exact rule.
        already = (
            db.query(PromotionLog).filter(PromotionLog.user_id == user.id, PromotionLog.rule_id == rule.id).first()
        )
        if already:
            continue

        # Check if user has certificates for every required course.
        required_course_ids = {
            row[0]
            for row in db.query(PromotionRuleRequirement.course_id)
            .filter(PromotionRuleRequirement.rule_id == rule.id)
            .all()
        }
        if not required_course_ids:
            continue  # A rule with no requirements should not trigger promotion.

        if required_course_ids.issubset(user_cert_course_ids):
            previous_role = user.role
            user.role = rule.target_role
            log = PromotionLog(
                user_id=user.id,
                rule_id=rule.id,
                previous_role=previous_role,
                new_role=rule.target_role,
            )
            db.add(log)
            db.commit()
            db.refresh(log)

            logger.info(
                "User %s promoted: %s → %s (rule: %s)",
                user.username,
                previous_role.value,
                rule.target_role.value,
                rule.name,
            )
            notify_promotion(user.username, rule.target_role.value, rule.name)
            sync_discord_role(user.discord_id, rule.target_role.value, previous_role.value)
            return log

    return None
