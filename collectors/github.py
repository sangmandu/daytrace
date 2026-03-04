import logging
import requests
from datetime import date

import config

logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"


def collect(target_date: date) -> dict:
    if not config.GITHUB_TOKEN or not config.GITHUB_USERNAME:
        logger.warning("GitHub config not set, skipping")
        return {"error": "GITHUB_TOKEN or GITHUB_USERNAME not set"}

    headers = {"Authorization": f"token {config.GITHUB_TOKEN}", "Accept": "application/vnd.github+json"}
    date_str = str(target_date)
    username = config.GITHUB_USERNAME

    commits = []
    prs_merged = []
    prs_opened = []
    reviews = 0

    resp = requests.get(f"{API_BASE}/users/{username}/events?per_page=100", headers=headers, timeout=30)
    resp.raise_for_status()

    for event in resp.json():
        created = event.get("created_at", "")[:10]
        if created != date_str:
            continue

        etype = event["type"]
        repo = event["repo"]["name"]

        if etype == "PushEvent":
            for c in event["payload"].get("commits", []):
                commits.append({"repo": repo, "message": c["message"].split("\n")[0]})
        elif etype == "PullRequestEvent":
            pr = event["payload"]["pull_request"]
            action = event["payload"]["action"]
            entry = {"repo": repo, "title": pr["title"], "number": pr["number"]}
            if action == "closed" and pr.get("merged"):
                prs_merged.append(entry)
            elif action == "opened":
                prs_opened.append(entry)
        elif etype == "PullRequestReviewEvent":
            reviews += 1

    return {
        "commits": commits,
        "prs_merged": prs_merged,
        "prs_opened": prs_opened,
        "reviews": reviews,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(collect(d))
