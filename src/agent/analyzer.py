"""Google Gemini-powered article analyzer: summary, companies, insurance angle."""
from __future__ import annotations

import json
import logging
import os
import time

import google.generativeai as genai

from src.prompts.analysis import SYSTEM_PROMPT, build_user_prompt
from src.scrapers.base import Article

logger = logging.getLogger(__name__)

MODEL = "gemini-1.5-flash"
INTER_CALL_DELAY = 1.0  # seconds between API calls


def analyze_article(article: Article, article_text: str) -> dict:
    """
    Call Gemini to generate summary, companies, and insurance angle for one article.

    Returns a dict with keys: summary, companies, angle.
    Returns empty-string fallback values on any failure.
    """
    fallback = {"summary": "", "companies": "", "angle": ""}

    if not article_text.strip():
        logger.warning("Empty article text for '%s'; skipping analysis", article.title)
        return fallback

    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=SYSTEM_PROMPT,
        )

        user_prompt = build_user_prompt(article.title, article_text)
        response = model.generate_content(user_prompt)
        raw = response.text.strip()
        return _parse_json_response(raw)

    except Exception as exc:
        err = str(exc)
        if "429" in err or "quota" in err.lower() or "rate" in err.lower():
            logger.warning("Gemini rate limit hit; waiting 30s then retrying '%s'", article.title)
            time.sleep(30)
            return analyze_article(article, article_text)

        logger.error("Gemini analysis failed for '%s': %s", article.title, exc)
        return fallback

    finally:
        time.sleep(INTER_CALL_DELAY)


def analyze_articles(articles: list[Article], fetch_text_fn) -> list[dict]:
    """
    Analyze a list of articles sequentially.

    fetch_text_fn: callable(url: str) -> str  (provided by BaseScraper.fetch_article_text)

    Returns a list of dicts, each containing the Article fields plus analysis.
    """
    results = []
    for article in articles:
        logger.info("Analyzing: %s", article.title[:80])
        article_text = fetch_text_fn(article.url)
        analysis = analyze_article(article, article_text)
        results.append(
            {
                "title": article.title,
                "url": article.url,
                "date": article.published_at.strftime("%Y-%m-%d"),
                "time": article.published_at.strftime("%H:%M"),
                "source": article.source,
                "summary": analysis.get("summary", ""),
                "companies": analysis.get("companies", ""),
                "angle": analysis.get("angle", ""),
            }
        )
    return results


def _parse_json_response(raw: str) -> dict:
    """Extract and parse the JSON object from Gemini's response."""
    # Strip markdown code fences if present
    if raw.startswith("```"):
        lines = raw.split("\n")
        raw = "\n".join(lines[1:-1]) if len(lines) > 2 else raw

    try:
        data = json.loads(raw)
        return {
            "summary": str(data.get("summary", "")).strip(),
            "companies": str(data.get("companies", "")).strip(),
            "angle": str(data.get("angle", "")).strip(),
        }
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse failed (%s); raw: %s", exc, raw[:200])
        return {"summary": "", "companies": "", "angle": ""}
