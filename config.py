import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

LINEAR_API_KEY = os.getenv("LINEAR_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_USERNAME = os.getenv("GITHUB_USERNAME", "")
SLACK_USER_TOKEN = os.getenv("SLACK_USER_TOKEN", "")
OBSIDIAN_VAULT_PATH = os.path.expanduser(os.getenv("OBSIDIAN_VAULT_PATH", ""))
OBSIDIAN_DAYTRACE_DIR = os.getenv("OBSIDIAN_DAYTRACE_DIR", "DayTrace")
CLAUDE_DIR = os.path.expanduser(os.getenv("CLAUDE_DIR", "~/.claude"))
