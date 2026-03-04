#!/usr/bin/env python3
import argparse
import json
import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import config
from collectors import linear, github, slack, claude
import summarizer
import writer

LOG_DIR = Path(__file__).parent / "logs"
LAST_RUN_FILE = Path(__file__).parent / ".last_run.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "daytrace.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("daytrace")


def get_target_dates(specific_date: date | None) -> list[date]:
    if specific_date:
        return [specific_date]

    yesterday = date.today() - timedelta(days=1)

    last_run = None
    if LAST_RUN_FILE.exists():
        try:
            data = json.loads(LAST_RUN_FILE.read_text())
            last_run = date.fromisoformat(data["last_date"])
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    if last_run and last_run < yesterday:
        dates = []
        d = last_run + timedelta(days=1)
        while d <= yesterday:
            dates.append(d)
            d += timedelta(days=1)
        return dates

    return [yesterday]


def save_last_run(d: date):
    LAST_RUN_FILE.write_text(json.dumps({"last_date": str(d)}))


def run_for_date(target_date: date):
    logger.info("Collecting data for %s", target_date)

    raw_data = {}
    for name, collector in [("linear", linear), ("github", github), ("slack", slack), ("claude", claude)]:
        try:
            raw_data[name] = collector.collect(target_date)
            logger.info("%s: OK", name)
        except Exception as e:
            logger.error("%s: FAILED - %s", name, e)
            raw_data[name] = {"error": str(e)}

    logger.info("Summarizing with Claude...")
    summary = summarizer.summarize(str(target_date), raw_data)

    writer.write(target_date, raw_data, summary)
    save_last_run(target_date)
    logger.info("Done: %s", target_date)


def main():
    LOG_DIR.mkdir(exist_ok=True)

    parser = argparse.ArgumentParser(description="DayTrace - Daily activity recorder")
    parser.add_argument("--date", type=date.fromisoformat, help="Specific date (YYYY-MM-DD)")
    args = parser.parse_args()

    dates = get_target_dates(args.date)
    logger.info("Processing %d date(s): %s", len(dates), [str(d) for d in dates])

    for d in dates:
        run_for_date(d)


if __name__ == "__main__":
    main()
