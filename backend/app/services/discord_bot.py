"""Discord Bot API service — manages Discord role sync for platform users.

Uses the Discord REST API (not a gateway bot) to assign/remove roles
when a user's platform role changes.
"""

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

DISCORD_API = "https://discord.com/api/v10"


def _get_role_map() -> dict[str, str]:
    """Parse DISCORD_ROLE_MAP env var into {platform_role: discord_role_id}."""
    if not settings.discord_role_map:
        return {}
    result = {}
    for pair in settings.discord_role_map.split(","):
        pair = pair.strip()
        if ":" not in pair:
            continue
        role, role_id = pair.split(":", 1)
        result[role.strip()] = role_id.strip()
    return result


def _bot_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bot {settings.discord_bot_token}",
        "Content-Type": "application/json",
    }


def _is_configured() -> bool:
    return bool(settings.discord_bot_token and settings.discord_guild_id and settings.discord_role_map)


def sync_discord_role(discord_id: str, new_role: str, previous_role: str | None = None) -> bool:
    """Sync a user's Discord role: remove old role (if any), add new role.

    Returns True if at least the new role was added successfully.
    """
    if not _is_configured():
        logger.debug("Discord bot not configured — skipping role sync")
        return False

    if not discord_id:
        logger.debug("User has no discord_id — skipping role sync")
        return False

    role_map = _get_role_map()
    new_discord_role_id = role_map.get(new_role)
    if not new_discord_role_id:
        logger.warning("No Discord role mapping for platform role '%s'", new_role)
        return False

    guild_id = settings.discord_guild_id
    headers = _bot_headers()
    success = False

    # Remove old role if mapped
    if previous_role:
        old_discord_role_id = role_map.get(previous_role)
        if old_discord_role_id and old_discord_role_id != new_discord_role_id:
            try:
                resp = httpx.delete(
                    f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}/roles/{old_discord_role_id}",
                    headers=headers,
                    timeout=10.0,
                )
                if resp.status_code in (200, 204):
                    logger.info("Removed Discord role %s from user %s", previous_role, discord_id)
                else:
                    logger.warning(
                        "Failed to remove Discord role %s from %s: %s %s",
                        previous_role,
                        discord_id,
                        resp.status_code,
                        resp.text[:200],
                    )
            except httpx.HTTPError:
                logger.exception("Error removing Discord role from %s", discord_id)

    # Add new role
    try:
        resp = httpx.put(
            f"{DISCORD_API}/guilds/{guild_id}/members/{discord_id}/roles/{new_discord_role_id}",
            headers=headers,
            timeout=10.0,
        )
        if resp.status_code in (200, 204):
            logger.info("Assigned Discord role %s to user %s", new_role, discord_id)
            success = True
        else:
            logger.warning(
                "Failed to assign Discord role %s to %s: %s %s",
                new_role,
                discord_id,
                resp.status_code,
                resp.text[:200],
            )
    except httpx.HTTPError:
        logger.exception("Error assigning Discord role to %s", discord_id)

    return success


def lookup_discord_member(discord_id: str) -> dict | None:
    """Look up a Discord guild member by user ID. Returns member data or None."""
    if not settings.discord_bot_token or not settings.discord_guild_id:
        return None

    try:
        resp = httpx.get(
            f"{DISCORD_API}/guilds/{settings.discord_guild_id}/members/{discord_id}",
            headers=_bot_headers(),
            timeout=10.0,
        )
        if resp.status_code == 200:
            return resp.json()
        return None
    except httpx.HTTPError:
        logger.exception("Error looking up Discord member %s", discord_id)
        return None
