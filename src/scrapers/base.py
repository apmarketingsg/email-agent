from __future__ import annotations

import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
}

REQUEST_TIMEOUT = 20
MAX_ARTICLE_TEXT_CHARS = 4000

# Tags whose content should be removed when extracting article text
_STRIP_TAGS = {
    "script", "style", "nav", "footer", "aside", "header",
    "noscript", "iframe", "form", "button", "figure",
}


@dataclass
class Article:
    title: str
    url: str
    published_at: datetime  # timezone-aware (SGT)
    source: str             # human-readable site name


class BaseScraper(ABC):
    """Abstract base class for all news site scrapers."""

    SOURCE_NAME: str = ""

    def get(self, url: str) -> str:
        """HTTP GET with standard headers. Returns response text or raises."""
        response = requests.get(url, headers=SCRAPER_HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.text

    def fetch_article_text(self, url: str) -> str:
        """
        Download a full article page and return clean body text.
        Strips navigation, ads, scripts etc. Truncates to MAX_ARTICLE_TEXT_CHARS.
        Returns empty string on failure.
        """
        try:
            html = self.get(url)
            soup = BeautifulSoup(html, "lxml")

            for tag in soup.find_all(_STRIP_TAGS):
                tag.decompose()

            # Try common article body selectors first
            for selector in (
                "article",
                '[class*="article-body"]',
                '[class*="article-content"]',
                '[class*="story-body"]',
                "main",
            ):
                container = soup.select_one(selector)
                if container:
                    text = container.get_text(separator=" ", strip=True)
                    if len(text) > 200:
                        return text[:MAX_ARTICLE_TEXT_CHARS]

            # Fallback: full page body text
            body = soup.find("body")
            if body:
                return body.get_text(separator=" ", strip=True)[:MAX_ARTICLE_TEXT_CHARS]
            return ""

        except Exception as exc:
            logger.warning("fetch_article_text failed for %s: %s", url, exc)
            return ""

    def _polite_delay(self) -> None:
        """Sleep 1–3 seconds between requests to be a polite scraper."""
        time.sleep(random.uniform(1.0, 3.0))

    @abstractmethod
    def scrape(self) -> list[Article]:
        """Return articles published in the last 8 hours."""
        ...
