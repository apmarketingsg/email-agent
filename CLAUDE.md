# CLAUDE.md — Email Agent

This file provides guidance for AI assistants (Claude and others) working in this repository. Keep it up to date as the project evolves.

---

## Project Overview

**email-agent** is a repository owned by `apmarketingsg`.

**Purpose:** An AI-powered Singapore business news digest agent. It scrapes 7 Singapore business news websites every 8 hours (00:00, 08:00, 16:00 SGT), enriches each article using Claude (30-word summary, companies identified, insurance-broker conversation angle), and emails a formatted HTML digest to the configured recipient.

---

## Current Repository State

```
email-agent/
├── src/
│   ├── scrapers/
│   │   ├── base.py                  # BaseScraper ABC + Article dataclass
│   │   ├── cna.py                   # Channel NewsAsia — Business
│   │   ├── business_times.py        # The Business Times — Singapore
│   │   ├── manufacturing_asia.py    # Manufacturing Asia
│   │   ├── sbr.py                   # Singapore Business Review
│   │   ├── abf.py                   # Asian Banking & Finance
│   │   ├── techinasia.py            # Tech in Asia — Singapore tag
│   │   └── theedge.py               # The Edge Singapore — News
│   ├── agent/
│   │   ├── analyzer.py              # Claude API: summary / companies / angle
│   │   └── db.py                    # SQLite deduplication store
│   ├── email/
│   │   ├── formatter.py             # HTML email table builder
│   │   └── sender.py                # Gmail SMTP sender
│   └── prompts/
│       └── analysis.py              # Versioned Claude prompt templates
├── data/                            # Runtime data — gitignored
│   └── sent_articles.db             # SQLite dedup DB (auto-created)
├── main.py                          # Scheduler entry point
├── run.sh                           # Cron wrapper for Namecheap shared hosting
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── CLAUDE.md
```

---

## Branch Conventions

- **`master`** — stable production branch; never commit directly
- **`claude/<task-id>`** — branches created by Claude Code for automated tasks
- Feature branches: `feat/<short-description>`
- Bug fix branches: `fix/<short-description>`

Always develop on the designated branch. Push with:

```bash
git push -u origin <branch-name>
```

---

## Development Setup

### Prerequisites

- Python 3.10+
- A Gmail account with an [App Password](https://support.google.com/accounts/answer/185833) enabled
- An Anthropic API key

### Bootstrap

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and fill in your values
cp .env.example .env
```

### Running

```bash
# Run a single digest immediately (for testing):
python main.py --once

# Start the scheduler (runs continuously at 00:00, 08:00, 16:00 SGT):
python main.py
```

---

## Deployment (Namecheap Shared Hosting / cPanel)

Shared hosting cannot run a persistent process, so `APScheduler` is bypassed.
Instead, three cPanel cron jobs each call `run.sh`, which runs `main.py --once`.

### One-time server setup (via cPanel → Terminal or SSH)

```bash
# 1. Upload / clone the repo into your home directory, e.g. ~/email-agent

# 2. Create virtualenv and install dependencies
cd ~/email-agent
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Create .env with your secrets
cp .env.example .env
nano .env          # fill in GEMINI_API_KEY, EMAIL_*, etc.

# 4. Make the wrapper executable
chmod +x run.sh

# 5. Smoke-test
bash run.sh
# Check data/logs/cron.log for output
```

### cPanel Cron Jobs

Go to **cPanel → Cron Jobs** and add three entries (replace `/home/USERNAME`
with your actual home path):

| Minute | Hour | Day | Month | Weekday | Command |
|--------|------|-----|-------|---------|---------|
| 0 | 16 | * | * | * | `/bin/bash /home/USERNAME/email-agent/run.sh` |
| 0 | 0  | * | * | * | `/bin/bash /home/USERNAME/email-agent/run.sh` |
| 0 | 8  | * | * | * | `/bin/bash /home/USERNAME/email-agent/run.sh` |

These UTC times equal 00:00, 08:00, 16:00 SGT (UTC+8).

Logs are written to `data/logs/cron.log` (gitignored).

---

## Environment Variables

All secrets live in `.env` (never committed). Copy `.env.example` and fill in:

| Variable | Purpose | Required |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini API key | Yes |
| `EMAIL_HOST` | SMTP server (default: `smtp.gmail.com`) | No |
| `EMAIL_PORT` | SMTP port (default: `587`) | No |
| `EMAIL_USER` | Gmail address | Yes |
| `EMAIL_PASS` | Gmail App Password | Yes |
| `EMAIL_FROM` | Sender address (defaults to `EMAIL_USER`) | No |
| `EMAIL_TO` | Recipient email address | Yes |

Add new variables to `.env.example` with placeholder values whenever they are introduced.

---

## Code Conventions

### Language & Runtime

**Python 3.10+** — chosen for its strong web scraping ecosystem (`requests`, `beautifulsoup4`, `feedparser`) and the `anthropic` SDK.

### Code Style

- Format with **Ruff** (`ruff format .`) before committing
- Lint with **Ruff** (`ruff check .`)
- Keep functions small and single-purpose
- Use `from __future__ import annotations` for forward-compatible type hints
- Tests live under `tests/`

### Commit Messages

Use conventional commits format:

```
<type>(<scope>): <short summary>

<optional body>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`

Examples:
```
feat(scrapers): add Business Times RSS feed support
fix(agent): handle Claude rate limit with exponential backoff
docs: update CLAUDE.md with run instructions
```

---

## Architecture

### Pipeline (per run)

1. **Scrape** — each of the 7 scrapers runs, returning `Article` objects from the last 8 hours (RSS feed first, HTML fallback)
2. **Deduplicate** — articles whose URLs are in `data/sent_articles.db` are skipped
3. **Analyze** — Claude (`claude-sonnet-4-6`) processes each new article to produce: summary (≤30 words), companies identified, insurance-broker angle (≤30 words)
4. **Mark sent** — processed article URLs are written to SQLite
5. **Format** — articles are rendered into an HTML email table grouped by source
6. **Send** — Gmail SMTP delivers the email to `EMAIL_TO`

### Scraper Design

Each scraper:
1. Tries RSS feeds first (more reliable, structured dates)
2. Falls back to HTML scraping with multiple CSS selector attempts
3. Filters to articles published in the last 8 hours
4. Adds a 1–3 second polite delay between HTTP requests

---

## AI / Agent Conventions

### LLM Usage

- Model: `gemini-1.5-flash` (free tier) for article analysis
- System prompts are versioned in `src/prompts/` — never hardcode prompts inline
- Each article gets one API call; responses must be valid JSON

### Security

- Never expose API keys or email passwords in logs or LLM context
- Article text is truncated to 3000 chars before sending to Claude (cost + injection surface control)
- Email credentials are read only from environment variables

---

## Testing

Run tests:

```bash
python -m pytest tests/
```

- Unit tests: pure functions (prompt building, HTML formatting, date parsing)
- Integration tests: mocked LLM responses and SMTP
- No real API calls in automated tests

---

## Key Dependencies

| Package | Purpose |
|---|---|
| `google-generativeai` | Google Gemini API client |
| `requests` | HTTP requests for scraping |
| `beautifulsoup4` + `lxml` | HTML parsing |
| `feedparser` | RSS/Atom feed parsing |
| `APScheduler` | Cron-style job scheduling |
| `python-dotenv` | `.env` file loading |
| `pytz` | SGT timezone support |

---

## What to Avoid

- Do not hardcode email addresses, passwords, or API keys anywhere in source files
- Do not add features beyond what is requested in the current task
- Do not delete files without confirming they are unused
- Do not push to `master` directly
- Do not commit `.env`, `data/`, `__pycache__/`, or log files

---

## Updating This File

Update CLAUDE.md whenever:

- New environment variables are added
- A new top-level directory or module is introduced
- Run or test commands change
- A significant architectural decision is made
