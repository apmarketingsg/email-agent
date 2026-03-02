"""Scraper for Channel NewsAsia — Business section."""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta

import feedparser
import pytz

from .base import Article, BaseScraper

logger = logging.getLogger(__name__)

SGT = pytz.timezone("Asia/Singapore")
LISTING_URL = "https://www.channelnewsasia.com/business"
RSS_URL = "https://www.channelnewsasia.com/api/v1/rss-outbound-feed?_format=xml&category=6511"
CUTOFF_HOURS = 8


class CNAScraper(BaseScraper):
    SOURCE_NAME = "Channel NewsAsia"

    def scrape(self) -> list[Article]:
        articles = self._scrape_rss()
        if not articles:
            logger.warning("CNA RSS returned no articles; falling back to HTML")
            articles = self._scrape_html()
        return articles

    def _scrape_rss(self) -> list[Article]:
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.bozo and not feed.entries:
                return []
            return _parse_feed_entries(feed.entries, self.SOURCE_NAME)
        except Exception as exc:
            logger.warning("CNA RSS failed: %s", exc)
            return []

    def _scrape_html(self) -> list[Article]:
        from bs4 import BeautifulSoup

        articles: list[Article] = []
        try:
            html = self.get(LISTING_URL)
            soup = BeautifulSoup(html, "lxml")
            cutoff = _cutoff_dt()

            for item in soup.select("article, .media-object, .list-object"):
                title_el = item.select_one("h3, h4, h5, h6, .list-object__heading-link")
                link_el = item.select_one("a[href]")
                time_el = item.select_one("time[datetime]")

                if not title_el or not link_el:
                    continue

                title = title_el.get_text(strip=True)
                url = link_el["href"]
                if not url.startswith("http"):
                    url = "https://www.channelnewsasia.com" + url

                published_at = _parse_datetime(time_el.get("datetime")) if time_el else None
                if published_at and published_at < cutoff:
                    continue
                if published_at is None:
                    published_at = datetime.now(tz=SGT)

                articles.append(Article(title=title, url=url, published_at=published_at, source=self.SOURCE_NAME))

            self._polite_delay()
        except Exception as exc:
            logger.warning("CNA HTML scrape failed: %s", exc)

        return articles


def _parse_feed_entries(entries: list, source_name: str) -> list[Article]:
    cutoff = _cutoff_dt()
    articles: list[Article] = []
    for entry in entries:
        published_at = _parse_struct_time(getattr(entry, "published_parsed", None))
        if published_at and published_at < cutoff:
            continue
        if published_at is None:
            published_at = datetime.now(tz=SGT)

        title = getattr(entry, "title", "").strip()
        url = getattr(entry, "link", "").strip()
        if not title or not url:
            continue

        articles.append(Article(title=title, url=url, published_at=published_at, source=source_name))
    return articles


def _parse_struct_time(struct: object | None) -> datetime | None:
    if struct is None:
        return None
    import time as _time
    try:
        ts = _time.mktime(struct)
        return datetime.fromtimestamp(ts, tz=timezone.utc).astimezone(SGT)
    except Exception:
        return None


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(SGT)
        except ValueError:
            continue
    return None


def _cutoff_dt() -> datetime:
    return datetime.now(tz=SGT) - timedelta(hours=CUTOFF_HOURS)
