"""HTML email formatter for the Singapore business news digest."""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime

import pytz

SGT = pytz.timezone("Asia/Singapore")

# ── Inline CSS constants (email-client safe) ─────────────────────────────────
_TABLE_STYLE = (
    "border-collapse:collapse;width:100%;min-width:900px;"
    "font-family:Arial,Helvetica,sans-serif;font-size:13px;"
)
_TH_STYLE = (
    "background:#1a1a2e;color:#ffffff;padding:10px 12px;"
    "text-align:left;border:1px solid #2d2d4e;white-space:nowrap;"
)
_TD_BASE = "padding:9px 12px;border:1px solid #d0d0d0;vertical-align:top;"
_TD_EVEN = _TD_BASE + "background:#f9f9f9;"
_TD_ODD = _TD_BASE + "background:#ffffff;"
_TD_LINK = "color:#1a73e8;text-decoration:none;font-weight:bold;"
_SECTION_STYLE = (
    "margin:24px 0 6px 0;font-family:Arial,Helvetica,sans-serif;"
    "font-size:15px;font-weight:bold;color:#1a1a2e;"
    "border-left:4px solid #1a73e8;padding-left:10px;"
)
_WRAPPER_STYLE = (
    "max-width:1100px;margin:0 auto;padding:20px;"
    "font-family:Arial,Helvetica,sans-serif;"
)
_HEADER_STYLE = (
    "background:#1a1a2e;color:#ffffff;padding:20px 24px;"
    "border-radius:6px 6px 0 0;margin-bottom:0;"
)
_FOOTER_STYLE = (
    "margin-top:24px;padding:16px;background:#f0f0f0;"
    "border-radius:4px;font-size:12px;color:#555;"
)


def build_html_email(enriched_articles: list[dict]) -> str:
    """
    Build a complete HTML email body from a list of enriched article dicts.

    Each dict must have keys:
        title, url, date, time, source, summary, companies, angle
    """
    now_sgt = datetime.now(tz=SGT)
    run_time = now_sgt.strftime("%d %b %Y, %I:%M %p SGT")

    body_parts: list[str] = []
    body_parts.append(_html_header(run_time, len(enriched_articles)))

    # Group articles by source
    grouped: dict[str, list[dict]] = defaultdict(list)
    for article in enriched_articles:
        grouped[article["source"]].append(article)

    for source, articles in grouped.items():
        body_parts.append(f'<p style="{_SECTION_STYLE}">{_esc(source)}</p>')
        body_parts.append(_build_table(articles))

    if not enriched_articles:
        body_parts.append(
            '<p style="font-family:Arial;color:#666;padding:20px 0;">'
            "No new articles found in the past 8 hours.</p>"
        )

    body_parts.append(_html_footer(enriched_articles))

    content = "\n".join(body_parts)
    return (
        "<!DOCTYPE html><html><head>"
        '<meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        "</head>"
        f'<body style="margin:0;padding:0;background:#e8e8e8;">'
        f'<div style="{_WRAPPER_STYLE}">{content}</div>'
        "</body></html>"
    )


def _html_header(run_time: str, total: int) -> str:
    return (
        f'<div style="{_HEADER_STYLE}">'
        '<h1 style="margin:0 0 6px 0;font-size:20px;font-weight:bold;">'
        "🇸🇬 Singapore Business News Digest</h1>"
        f'<p style="margin:0;font-size:13px;opacity:0.85;">'
        f"Generated: {run_time} &nbsp;·&nbsp; {total} new article{'s' if total != 1 else ''}"
        "</p></div>"
    )


def _build_table(articles: list[dict]) -> str:
    headers = ["Date", "Time", "Title", "Summary", "Companies", "Insurance Angle"]
    header_row = "".join(f'<th style="{_TH_STYLE}">{h}</th>' for h in headers)

    rows: list[str] = []
    for i, art in enumerate(articles):
        td = _TD_EVEN if i % 2 == 0 else _TD_ODD
        title_cell = (
            f'<a href="{_esc(art["url"])}" style="{_TD_LINK}" target="_blank">'
            f'{_esc(art["title"])}</a>'
        )
        row_cells = [
            f'<td style="{td}">{_esc(art["date"])}</td>',
            f'<td style="{td}">{_esc(art["time"])}</td>',
            f'<td style="{td}">{title_cell}</td>',
            f'<td style="{td};max-width:220px;">{_esc(art["summary"])}</td>',
            f'<td style="{td};max-width:160px;">{_esc(art["companies"])}</td>',
            f'<td style="{td};max-width:220px;">{_esc(art["angle"])}</td>',
        ]
        rows.append(f'<tr>{"".join(row_cells)}</tr>')

    all_rows = "\n".join(rows)
    return (
        '<div style="overflow-x:auto;">'
        f'<table style="{_TABLE_STYLE}">'
        f"<thead><tr>{header_row}</tr></thead>"
        f"<tbody>{all_rows}</tbody>"
        "</table></div>"
    )


def _html_footer(articles: list[dict]) -> str:
    sources = sorted({a["source"] for a in articles})
    source_list = ", ".join(_esc(s) for s in sources) if sources else "—"
    return (
        f'<div style="{_FOOTER_STYLE}">'
        "<strong>Sources monitored:</strong> "
        f"{source_list}<br>"
        "<small>This digest is generated automatically every 8 hours at "
        "00:00, 08:00, and 16:00 SGT.</small>"
        "</div>"
    )


def _esc(text: str) -> str:
    """Minimal HTML escaping for plain-text values."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
