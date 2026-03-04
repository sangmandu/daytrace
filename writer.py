import logging
from datetime import date
from pathlib import Path

import yaml

import config

logger = logging.getLogger(__name__)

WEEKDAYS_KO = ["월", "화", "수", "목", "금", "토", "일"]


def write(target_date: date, raw_data: dict, summary: str):
    vault = Path(config.OBSIDIAN_VAULT_PATH)
    if not vault.exists():
        logger.error("Obsidian vault not found: %s", vault)
        return

    out_dir = vault / config.OBSIDIAN_DAYTRACE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    filepath = out_dir / f"{target_date}.md"

    weekday = WEEKDAYS_KO[target_date.weekday()]

    linear = raw_data.get("linear", {})
    slack = raw_data.get("slack", {})
    claude = raw_data.get("claude", {})
    github = raw_data.get("github", {})

    frontmatter = {
        "date": str(target_date),
        "tracker": True,
        "linear_completed": len(linear.get("completed", [])),
        "github_commits": len(github.get("commits", [])),
        "slack_messages": slack.get("total", 0),
        "claude_sessions": claude.get("sessions", 0),
    }

    lines = ["---"]
    lines.append(yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True).strip())
    lines.append("---")
    lines.append(f"# {target_date} ({weekday})\n")
    lines.append(summary)

    filepath.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Written: %s", filepath)
