"""
Singapore Business News Email Agent — Entry Point

Schedules the digest to run at 00:00, 08:00, and 16:00 SGT every day.

Usage:
    # Run the scheduler (keeps running):
    python main.py

    # Run a single digest immediately (for testing):
    python main.py --once
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

load_dotenv()

from src.scrapers.cna import CNAScraper
from src.scrapers.business_times import BusinessTimesScraper
from src.scrapers.manufacturing_asia import ManufacturingAsiaScraper
from src.scrapers.sbr import SBRScraper
from src.scrapers.abf import ABFScraper
from src.scrapers.techinasia import TechInAsiaScraper
from src.scrapers.theedge import TheEdgeSingaporeScraper
from src.scrapers.base import BaseScraper, Article
from src.agent.analyzer import analyze_articles
from src.agent.db import is_sent, mark_sent, cleanup_old_records
from src.email.formatter import build_html_email
from src.email.sender import send_email

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SGT = pytz.timezone("Asia/Singapore")

ALL_SCRAPERS: list[type[BaseScraper]] = [
    CNAScraper,
    BusinessTimesScraper,
    ManufacturingAsiaScraper,
    SBRScraper,
    ABFScraper,
    TechInAsiaScraper,
    TheEdgeSingaporeScraper,
]


def run_digest() -> None:
    """Full pipeline: scrape → deduplicate → analyze → format → send."""
    logger.info("=== Digest run started ===")
    cleanup_old_records()

    # 1. Scrape all sources
    all_articles: list[Article] = []
    for scraper_cls in ALL_SCRAPERS:
        scraper = scraper_cls()
        try:
            articles = scraper.scrape()
            logger.info("%s → %d article(s)", scraper.SOURCE_NAME, len(articles))
            all_articles.extend(articles)
        except Exception as exc:
            logger.error("Scraper %s failed: %s", scraper_cls.__name__, exc)

    if not all_articles:
        logger.info("No articles found from any source.")
        return

    # 2. Deduplicate against already-sent articles
    new_articles = [a for a in all_articles if not is_sent(a.url)]
    logger.info("%d new article(s) after deduplication (of %d total)", len(new_articles), len(all_articles))

    if not new_articles:
        logger.info("All articles already sent. Nothing to do.")
        return

    # 3. Analyze each article with Gemini (summary, companies, angle)
    scraper_instance = CNAScraper()  # use BaseScraper's fetch_article_text
    enriched = analyze_articles(new_articles, scraper_instance.fetch_article_text)

    # 4. Mark all as sent
    for article in new_articles:
        mark_sent(article.url, article.title)

    # 5. Build email
    now_sgt = datetime.now(tz=SGT)
    subject = f"SG Business News Digest — {now_sgt.strftime('%d %b %Y, %I:%M %p')} SGT"
    html_body = build_html_email(enriched)

    # 6. Send email (skip if no EMAIL_TO configured)
    if os.environ.get("EMAIL_TO"):
        try:
            send_email(html_body, subject)
            logger.info("Email sent: %d article(s)", len(enriched))
        except Exception as exc:
            logger.error("Failed to send email: %s", exc)
    else:
        logger.warning("EMAIL_TO not set — email not sent. Set it in .env to enable delivery.")

    logger.info("=== Digest run complete ===")


def main() -> None:
    parser = argparse.ArgumentParser(description="Singapore Business News Email Agent")
    parser.add_argument("--once", action="store_true", help="Run one digest immediately and exit")
    args = parser.parse_args()

    _validate_env()

    if args.once:
        run_digest()
        return

    # Run scheduler: midnight, 8am, 4pm SGT
    scheduler = BlockingScheduler(timezone=SGT)
    scheduler.add_job(run_digest, "cron", hour="0,8,16", minute=0)
    logger.info("Scheduler started. Digest runs at 00:00, 08:00, 16:00 SGT.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def _validate_env() -> None:
    required = ["GEMINI_API_KEY", "EMAIL_USER", "EMAIL_PASS", "EMAIL_TO"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        logger.error("Missing required environment variables: %s", ", ".join(missing))
        logger.error("Copy .env.example to .env and fill in your values.")
        sys.exit(1)


if __name__ == "__main__":
    main()
