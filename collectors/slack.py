import logging
import requests
from datetime import date

import config

logger = logging.getLogger(__name__)


def collect(target_date: date) -> dict:
    if not config.SLACK_USER_TOKEN:
        logger.warning("SLACK_USER_TOKEN not set, skipping")
        return {"error": "SLACK_USER_TOKEN not set"}

    headers = {"Authorization": f"Bearer {config.SLACK_USER_TOKEN}"}

    all_matches = []
    page = 1
    while True:
        resp = requests.get(
            "https://slack.com/api/search.messages",
            params={"query": f"from:me on:{target_date.isoformat()}", "count": 100, "page": page},
            headers=headers,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        if not data.get("ok"):
            logger.error("Slack API error: %s", data.get("error"))
            return {"error": data.get("error", "unknown")}

        matches = data.get("messages", {}).get("matches", [])
        all_matches.extend(matches)

        pages = data.get("messages", {}).get("paging", {}).get("pages", 1)
        if page >= pages:
            break
        page += 1

    by_channel: dict[str, dict] = {}
    total = 0
    for m in all_matches:
        ch = m.get("channel", {})
        if ch.get("is_im") or ch.get("is_mpim"):
            continue
        total += 1
        name = ch.get("name", "unknown")
        if name not in by_channel:
            by_channel[name] = {"count": 0, "messages": []}
        by_channel[name]["count"] += 1
        text = m.get("text", "").strip()
        if text and len(by_channel[name]["messages"]) < 5:
            by_channel[name]["messages"].append(text[:150])

    return {"total": total, "by_channel": by_channel}


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(collect(d))
