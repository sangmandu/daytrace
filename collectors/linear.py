import logging
import requests
from datetime import date

import config

logger = logging.getLogger(__name__)

GRAPHQL_URL = "https://api.linear.app/graphql"

QUERY = """
query($after: DateTimeOrDuration!, $before: DateTimeOrDuration!) {
  issues(
    filter: {
      updatedAt: { gte: $after, lt: $before }
      assignee: { isMe: { eq: true } }
    }
    first: 100
  ) {
    nodes {
      identifier
      title
      state { name type }
      createdAt
      completedAt
    }
  }
  comments(
    filter: {
      createdAt: { gte: $after, lt: $before }
      user: { isMe: { eq: true } }
    }
    first: 100
  ) {
    nodes { id }
  }
}
"""


def collect(target_date: date) -> dict:
    if not config.LINEAR_API_KEY:
        logger.warning("LINEAR_API_KEY not set, skipping")
        return {"error": "LINEAR_API_KEY not set"}

    after = f"{target_date}T00:00:00.000Z"
    before = f"{target_date + __import__('datetime').timedelta(days=1)}T00:00:00.000Z"

    headers = {"Authorization": config.LINEAR_API_KEY, "Content-Type": "application/json"}
    resp = requests.post(GRAPHQL_URL, json={"query": QUERY, "variables": {"after": after, "before": before}}, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    if "errors" in data:
        logger.error("Linear API errors: %s", data["errors"])
        return {"error": str(data["errors"])}

    issues = data["data"]["issues"]["nodes"]
    comments = data["data"]["comments"]["nodes"]

    completed = [{"id": i["identifier"], "title": i["title"]} for i in issues if i["state"]["type"] == "completed"]
    in_progress = [{"id": i["identifier"], "title": i["title"]} for i in issues if i["state"]["type"] == "started"]
    created = [{"id": i["identifier"], "title": i["title"]} for i in issues if i["createdAt"].startswith(str(target_date))]

    return {
        "completed": completed,
        "in_progress": in_progress,
        "created": created,
        "comments": len(comments),
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    print(collect(d))
