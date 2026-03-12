#!/bin/bash
# discord-notify.sh — Send CI/CD status notifications to Discord via webhook
# Usage: ./scripts/discord-notify.sh --status success --title "CI: feat: add login" ...
set -euo pipefail

# --- Defaults -----------------------------------------------------------------
STATUS=""
TITLE=""
REPO=""
COMMIT=""
AUTHOR=""
URL=""
WEBHOOK_URL="${DISCORD_WEBHOOK_CI:-}"

# --- Parse arguments ----------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --status)  STATUS="$2";  shift 2 ;;
        --title)   TITLE="$2";   shift 2 ;;
        --repo)    REPO="$2";    shift 2 ;;
        --commit)  COMMIT="$2";  shift 2 ;;
        --author)  AUTHOR="$2";  shift 2 ;;
        --url)     URL="$2";     shift 2 ;;
        --webhook) WEBHOOK_URL="$2"; shift 2 ;;
        *)         echo "Unknown option: $1" >&2; exit 1 ;;
    esac
done

# --- Validate -----------------------------------------------------------------
if [ -z "$WEBHOOK_URL" ]; then
    echo "DISCORD_WEBHOOK_CI not set and --webhook not provided; skipping notification."
    exit 0
fi

if [ -z "$STATUS" ]; then
    echo "Error: --status is required (success|failure|cancelled)" >&2
    exit 1
fi

# --- Build embed --------------------------------------------------------------
SHORT_COMMIT="${COMMIT:0:7}"
TITLE="${TITLE:-CI/CD notification}"

case "$STATUS" in
    success)
        COLOR=3066993   # green (#2ecc71)
        EMOJI="✅"
        STATUS_TEXT="Sikeres"
        ;;
    failure)
        COLOR=15158332  # red (#e74c3c)
        EMOJI="❌"
        STATUS_TEXT="Sikertelen"
        ;;
    cancelled)
        COLOR=9807270   # grey (#95a5a6)
        EMOJI="⚪"
        STATUS_TEXT="Megszakítva"
        ;;
    *)
        COLOR=3447003   # blue (#3498db)
        EMOJI="ℹ️"
        STATUS_TEXT="$STATUS"
        ;;
esac

# Build JSON payload — construct URL field directly in the heredoc
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# Sanitize inputs — remove characters that break JSON
sanitize() {
    printf '%s' "$1" | tr -d '"\\' | head -c 256
}

S_TITLE=$(sanitize "$TITLE")
S_REPO=$(sanitize "$REPO")
S_AUTHOR=$(sanitize "$AUTHOR")
S_URL=$(sanitize "$URL")

# Build URL line conditionally
URL_LINE=""
if [ -n "$S_URL" ]; then
    URL_LINE="\"url\": \"${S_URL}\","
fi

PAYLOAD=$(cat <<EOF
{
  "embeds": [{
    ${URL_LINE}
    "title": "${EMOJI} ${S_TITLE}",
    "color": ${COLOR},
    "fields": [
      {"name": "Státusz", "value": "${STATUS_TEXT}", "inline": true},
      {"name": "Commit", "value": "\`${SHORT_COMMIT}\`", "inline": true},
      {"name": "Szerző", "value": "${S_AUTHOR}", "inline": true},
      {"name": "Repó", "value": "${S_REPO}", "inline": false}
    ],
    "timestamp": "${TIMESTAMP}"
  }]
}
EOF
)

# --- Send ---------------------------------------------------------------------
HTTP_CODE=$(curl -s -o /tmp/discord_response.txt -w "%{http_code}" -X POST "$WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d "$PAYLOAD")

if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
    echo "Discord notification sent (HTTP $HTTP_CODE)"
else
    echo "Discord notification failed (HTTP $HTTP_CODE)" >&2
    echo "Response: $(cat /tmp/discord_response.txt 2>/dev/null)" >&2
    exit 1
fi
