"""Scraper for The Business Times — Singapore section."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

import feedparser
import pytz
from bs4 import BeautifulSoup

from .base import Article, BaseScraper
from .cna import _parse_feed_entries, _parse_datetime, _cutoff_dt

logger = logging.getLogger(__name__)

SGT = pytz.timezone("Asia/Singapore")
LISTING_URL = "https://www.businesstimes.com.sg/singapore"
RSS_URLS = [
    "https://www.businesstimes.com.sg/rss/singapore",
    "https://www.businesstimes.com.sg/rss/all",
]
CUTOFF_HOURS = 8


class BusinessTimesScraper(BaseScraper):
    SOURCE_NAME = "The Business Times"

    def scrape(self) -> list[Article]:
        for rss_url in RSS_URLS:
            articles = self._scrape_rss(rss_url)
            if articles:
                return articles
        logger.warning("Business Times RSS returned nothing; falling back to HTML")
        return self._scrape_html()

    def _scrape_rss(self, rss_url: str) -> list[Article]:
        try:
            feed = feedparser.parse(rss_url)
            if feed.bozo and not feed.entries:
                return []
            return _parse_feed_entries(feed.entries, self.SOURCE_NAME)
        except Exception as exc:
            logger.warning("Business Times RSS (%s) failed: %s", rss_url, exc)
            return []

    def _scrape_html(self) -> list[Article]:
        articles: list[Article] = []
        try:
            html = self.get(LISTING_URL)
            soup = BeautifulSoup(html, "lxml")
            cutoff = _cutoff_dt()

            selectors = [
                "article",
                ".story-card",
                ".article-card",
                '[class*="article"]',
                '[class*="story"]',
            ]
            items = []
            for sel in selectors:
                items = soup.select(sel)
                if items:
                    break

            for item in items:
                title_el = item.select_one("h2, h3, h4, [class*='title'], [class*='heading']")
                link_el = item.select_one("a[href]")
                time_el = item.select_one("time[datetime]")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                url = link_el["href"]
                if not url.startswith("http"):
                    url = "https://www.businesstimes.com.sg" + url

                published_at = _parse_datetime(time_el.get("datetime")) if time_el else None
                if published_at and published_at < cutoff:
                    continue
                if published_at is None:
                    published_at = datetime.now(tz=SGT)

                articles.append(Article(title=title, url=url, published_at=published_at, source=self.SOURCE_NAME))

            self._polite_delay()
        except Exception as exc:
            logger.warning("Business Times HTML scrape failed: %s", exc)

        return articles
