import json
import logging
import os
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

import config

logger = logging.getLogger(__name__)

PERSONAL_KEYWORDS = {"stock", "daytrace", "relay-test", "relay-test2", "Downloads", "hedzup"}


def _is_work_project(project_name: str, cwd: str) -> bool:
    for kw in PERSONAL_KEYWORDS:
        if kw in project_name or kw in cwd:
            return False
    if cwd.startswith("/private/tmp"):
        return False
    return True


def _normalize_project_name(raw: str) -> str:
    raw = raw.replace("-Users-mini-", "")
    raw = raw.replace("-", "_")
    return raw


def _get_date_from_entry(entry: dict) -> date | None:
    snap = entry.get("snapshot", {})
    ts = snap.get("timestamp")
    if not ts:
        msg = entry.get("message", {})
        if isinstance(msg, dict):
            ts = msg.get("created_at")
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.date()
    except (ValueError, AttributeError):
        return None


def _extract_user_text(msg: dict) -> str:
    content = msg.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        texts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                texts.append(block.get("text", ""))
        return " ".join(texts).strip()
    return ""


def collect(target_date: date) -> dict:
    claude_dir = Path(config.CLAUDE_DIR)
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        logger.warning("Claude projects dir not found: %s", projects_dir)
        return {"error": f"Directory not found: {projects_dir}"}

    project_stats: dict[str, dict] = defaultdict(lambda: {
        "sessions": set(),
        "prompts": 0,
        "first_messages": {},
    })

    for jsonl_file in projects_dir.rglob("*.jsonl"):
        mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime, tz=timezone.utc).date()
        if abs((mtime - target_date).days) > 2:
            continue

        folder_name = jsonl_file.parent.name
        if folder_name == "subagents":
            continue

        file_has_target = False
        file_cwd = ""
        file_user_msgs = 0
        file_session_ids = set()
        first_user_msg = ""

        try:
            with open(jsonl_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if not file_cwd:
                        cwd = entry.get("cwd", "")
                        if cwd:
                            file_cwd = cwd

                    entry_date = _get_date_from_entry(entry)
                    if entry_date == target_date:
                        file_has_target = True

                    if not file_has_target:
                        continue

                    sid = entry.get("sessionId", jsonl_file.stem)
                    file_session_ids.add(sid)

                    msg = entry.get("message", {})
                    if isinstance(msg, dict) and msg.get("role") == "user":
                        text = _extract_user_text(msg)
                        if text:
                            file_user_msgs += 1
                            if not first_user_msg:
                                first_user_msg = text[:200]
        except Exception as e:
            logger.debug("Error reading %s: %s", jsonl_file, e)
            continue

        if not file_has_target:
            continue

        proj_key = _normalize_project_name(folder_name)

        if not _is_work_project(folder_name, file_cwd):
            continue

        stats = project_stats[proj_key]
        stats["sessions"].update(file_session_ids)
        stats["prompts"] += file_user_msgs
        for sid in file_session_ids:
            if sid not in stats["first_messages"] and first_user_msg:
                stats["first_messages"][sid] = first_user_msg

    projects_summary = []
    total_sessions = set()
    total_prompts = 0

    for proj, stats in sorted(project_stats.items()):
        total_sessions.update(stats["sessions"])
        total_prompts += stats["prompts"]
        projects_summary.append({
            "name": proj,
            "sessions": len(stats["sessions"]),
            "prompts": stats["prompts"],
            "activities": list(stats["first_messages"].values()),
        })

    return {
        "sessions": len(total_sessions),
        "prompts": total_prompts,
        "projects": projects_summary,
    }


if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    d = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    result = collect(d)
    print(json.dumps(result, indent=2, ensure_ascii=False))
