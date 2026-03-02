# CLAUDE.md — Email Agent

This file provides guidance for AI assistants (Claude and others) working in this repository. Keep it up to date as the project evolves.

---

## Project Overview

**email-agent** is a repository owned by `apmarketingsg`. As of the initial commit (2026-03-02), the project is freshly initialized and contains no source code yet.

**Intended purpose:** An AI-powered email agent — likely responsible for reading, processing, drafting, or automating email workflows using LLM capabilities.

---

## Current Repository State

```
email-agent/
├── README.md      # Minimal placeholder
└── CLAUDE.md      # This file
```

No source code, dependencies, tests, CI/CD, or configuration files exist yet. All structure below represents conventions to follow **as the project is built out**.

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

## Development Setup (to be implemented)

When dependencies are added, document setup steps here. Typical bootstrap:

```bash
# Install dependencies (Node.js example)
npm install

# Copy environment template
cp .env.example .env

# Run development server
npm run dev

# Run tests
npm test
```

---

## Environment Variables

Document all required environment variables in `.env.example`. **Never commit `.env` files.** Expected variables for an email agent typically include:

| Variable | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API access |
| `EMAIL_HOST` | SMTP/IMAP server host |
| `EMAIL_PORT` | Server port |
| `EMAIL_USER` | Email account username |
| `EMAIL_PASS` | Email account password |
| `EMAIL_FROM` | Sender address |

Add new variables to `.env.example` with placeholder values whenever they are introduced.

---

## Code Conventions

### Language & Runtime

Document the chosen language/runtime here once decided. Recommended defaults for an email agent:

- **Node.js + TypeScript** — strong ecosystem for email (`nodemailer`, `imapflow`) and AI SDKs
- **Python** — alternative if data processing or ML tasks dominate

### File Structure (recommended)

```
src/
├── agent/          # Core agent logic (LLM orchestration, tool use)
├── email/          # Email read/send/parse utilities
├── tools/          # Agent tools (search, calendar, CRM, etc.)
├── prompts/        # System prompts and prompt templates
├── types/          # Shared TypeScript types/interfaces
└── index.ts        # Entry point
tests/
├── unit/
└── integration/
```

### Code Style

- Follow the linter/formatter config in the repository (ESLint + Prettier for TS, Ruff for Python)
- Run lint and format before committing
- Prefer explicit types over `any` in TypeScript
- Keep functions small and single-purpose
- Co-locate tests with source files (`*.test.ts`) or place them under `tests/`

### Commit Messages

Use the conventional commits format:

```
<type>(<scope>): <short summary>

<optional body>
```

Types: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `ci`

Examples:
```
feat(email): add IMAP inbox polling with idle support
fix(agent): handle rate limit errors from Anthropic API
docs: update CLAUDE.md with environment variables
```

---

## AI / Agent Conventions

Since this is an AI-powered agent, follow these practices:

### LLM Usage

- Default to `claude-sonnet-4-6` for general tasks; use `claude-haiku-4-5-20251001` for high-throughput, low-latency calls
- Always pass system prompts from versioned files in `src/prompts/`, not hardcoded strings
- Log all LLM inputs/outputs in development for debugging (strip in production or use structured logging)

### Tool Use

- Define agent tools with clear `name`, `description`, and `input_schema`
- Validate all tool inputs before execution
- Handle tool errors gracefully and return structured error messages to the agent

### Security

- Never expose raw email credentials or API keys in logs or LLM context
- Sanitize email content before passing to the LLM to avoid prompt injection
- Limit tool permissions to least privilege (e.g., read-only email access unless write is needed)

---

## Testing

- Write unit tests for all pure functions (email parsing, prompt building, etc.)
- Write integration tests for agent workflows using mocked LLM responses
- Do not make real API calls in automated tests; use recorded fixtures or mocks
- Target ≥80% coverage on core agent and email modules

Run tests:

```bash
npm test            # unit tests
npm run test:int    # integration tests
```

---

## CI/CD

Add a GitHub Actions workflow at `.github/workflows/ci.yml` when the project is ready. It should:

1. Install dependencies
2. Run linter
3. Run type-check
4. Run tests
5. Build (if applicable)

---

## Key Dependencies (to be added)

| Package | Purpose |
|---|---|
| `@anthropic-ai/sdk` | Anthropic Claude API client |
| `nodemailer` | SMTP email sending |
| `imapflow` | IMAP email reading |
| `zod` | Schema validation for tool inputs |
| `dotenv` | Environment variable loading |

---

## What to Avoid

- Do not hardcode email addresses, passwords, or API keys anywhere in source files
- Do not add features beyond what is requested in the current task
- Do not delete files without confirming they are unused
- Do not push to `master` directly
- Do not commit `.env`, `node_modules/`, build artifacts, or log files

---

## Updating This File

Update CLAUDE.md whenever:

- New environment variables are added
- A new top-level directory is introduced
- Build, test, or run commands change
- A significant architectural decision is made

Keep this file accurate — it is the primary reference for AI assistants working in this codebase.
