import asyncio
import json
import logging
import os
from pathlib import Path

from claude_agent_sdk import query
from claude_agent_sdk.types import ClaudeAgentOptions, ResultMessage

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).parent / "prompts" / "daily_summary.md"


async def _run_query(full_prompt: str) -> str:
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    options = ClaudeAgentOptions(
        env=env,
        model="haiku",
        max_turns=1,
        permission_mode="bypassPermissions",
        system_prompt=PROMPT_PATH.read_text(encoding="utf-8"),
    )

    result_text = ""
    async for message in query(prompt=full_prompt, options=options):
        if isinstance(message, ResultMessage):
            result_text = message.result

    return result_text


def summarize(date_str: str, raw_data: dict) -> str:
    user_prompt = f"Date: {date_str}\n\nRaw activity data:\n```json\n{json.dumps(raw_data, indent=2, ensure_ascii=False)}\n```"

    os.environ.pop("CLAUDECODE", None)

    try:
        result = asyncio.run(_run_query(user_prompt))
        if result.strip():
            return result.strip()
        logger.warning("Agent SDK returned empty result")
        return _fallback_summary(raw_data)
    except Exception as e:
        logger.error("Agent SDK failed: %s", e)
        return _fallback_summary(raw_data)


def _fallback_summary(raw_data: dict) -> str:
    lines = []

    linear = raw_data.get("linear", {})
    if linear.get("completed") or linear.get("in_progress") or linear.get("created"):
        lines.append("## Linear")
        for i in linear.get("completed", []):
            lines.append(f"- [Completed] {i['id']} {i['title']}")
        for i in linear.get("in_progress", []):
            lines.append(f"- [In Progress] {i['id']} {i['title']}")
        for i in linear.get("created", []):
            lines.append(f"- [Created] {i['id']} {i['title']}")
        lines.append("")

    slack = raw_data.get("slack", {})
    if slack.get("total", 0) > 0:
        lines.append("## Slack")
        lines.append(f"Messages: {slack['total']}")
        lines.append("")

    claude = raw_data.get("claude", {})
    if claude.get("sessions", 0) > 0:
        lines.append("## Claude Code")
        for p in claude.get("projects", []):
            if isinstance(p, dict):
                lines.append(f"- {p['name']}: {p['sessions']} sessions")
        lines.append("")

    return "\n".join(lines) if lines else "*No work activity recorded.*"
