"""Scraper for Singapore Business Review — Singapore market section."""
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
LISTING_URL = "https://sbr.com.sg/market/singapore"
RSS_URLS = [
    "https://sbr.com.sg/feed",
    "https://sbr.com.sg/rss.xml",
    "https://sbr.com.sg/rss",
]
CUTOFF_HOURS = 8


class SBRScraper(BaseScraper):
    SOURCE_NAME = "Singapore Business Review"

    def scrape(self) -> list[Article]:
        for rss_url in RSS_URLS:
            articles = self._scrape_rss(rss_url)
            if articles:
                return articles
        logger.warning("SBR RSS failed; falling back to HTML")
        return self._scrape_html()

    def _scrape_rss(self, rss_url: str) -> list[Article]:
        try:
            feed = feedparser.parse(rss_url)
            if feed.bozo and not feed.entries:
                return []
            return _parse_feed_entries(feed.entries, self.SOURCE_NAME)
        except Exception as exc:
            logger.warning("SBR RSS (%s) failed: %s", rss_url, exc)
            return []

    def _scrape_html(self) -> list[Article]:
        articles: list[Article] = []
        try:
            html = self.get(LISTING_URL)
            soup = BeautifulSoup(html, "lxml")
            cutoff = _cutoff_dt()

            selectors = [
                "article",
                ".article-card",
                ".news-card",
                '[class*="article"]',
                '[class*="news"]',
            ]
            items = []
            for sel in selectors:
                items = soup.select(sel)
                if len(items) > 2:
                    break

            for item in items:
                title_el = item.select_one("h2, h3, h4, [class*='title'], [class*='heading']")
                link_el = item.select_one("a[href]")
                time_el = item.select_one("time[datetime], [class*='date'], [class*='time']")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                url = link_el["href"]
                if not url.startswith("http"):
                    url = "https://sbr.com.sg" + url

                published_at = None
                if time_el:
                    published_at = _parse_datetime(time_el.get("datetime") or time_el.get_text(strip=True))
                if published_at and published_at < cutoff:
                    continue
                if published_at is None:
                    published_at = datetime.now(tz=SGT)

                articles.append(Article(title=title, url=url, published_at=published_at, source=self.SOURCE_NAME))

            self._polite_delay()
        except Exception as exc:
            logger.warning("SBR HTML scrape failed: %s", exc)

        return articles
