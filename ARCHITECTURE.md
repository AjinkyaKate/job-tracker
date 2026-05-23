# Architecture — How the Pieces Fit

> Read this when you forget how the system is shaped. Updated as we build.

## The mental model

```
   ┌──────────────┐         ┌──────────────────┐         ┌─────────────┐
   │   Browser    │  HTTP   │   FastAPI app    │   SQL   │  Database   │
   │  (frontend)  │ ──────► │   (backend)      │ ──────► │  (SQLite →  │
   │              │ ◄────── │                  │ ◄────── │   Postgres) │
   └──────────────┘         └────────┬─────────┘         └─────────────┘
                                     │
                                     │ HTTPS
                                     ▼
                            ┌──────────────────┐
                            │  Claude API      │
                            │  (extract JDs,   │
                            │   match resumes) │
                            └──────────────────┘
                                     │
                                     │ optional
                                     ▼
                            ┌──────────────────┐
                            │  Local files     │
                            │  (resume PDFs)   │
                            └──────────────────┘
```

## Components

### 1. Frontend (Phase 3+)
- **What:** the web pages the user sees in a browser
- **Tech:** HTML + Tailwind (via CDN) + HTMX
- **Why HTMX:** lets you build interactive UIs by adding attributes to HTML, no separate JS app needed. Perfect for solo PM-builder.
- **Served by:** the FastAPI backend itself (no separate frontend server in early phases)

### 2. Backend (Phase 1+)
- **What:** the program that does the work — receives requests, talks to the DB, calls AI, returns data
- **Tech:** Python + FastAPI
- **Why FastAPI:** modern, fast, auto-generates API docs at `/docs`, uses Python type hints (which teach you typing as a side effect), much less boilerplate than Django/Flask
- **Phase 1 form:** CLI script (no HTTP yet) — same Python codebase, just driven by argparse
- **Phase 3 form:** add FastAPI on top, reuse the core functions

### 3. Database
- **Phase 1–2:** SQLite — a single file on disk, no server, zero config. Perfect for learning SQL.
- **Phase 4+:** Postgres on Supabase — free tier, web dashboard, accessible from a deployed app
- **Why this progression:** SQLite to learn schema design without networking pain; Postgres when you need cloud access

### 4. AI service
- **What:** the brain. Reads JDs, extracts structured fields, recommends resume variants.
- **Tech:** Anthropic Claude API via the `anthropic` Python SDK
- **Pattern:** structured-output prompting — ask Claude to return JSON conforming to a schema, parse it, validate, save.
- **Cost mental model:** at small scale (~50 jobs/week), this is cents per week. Set a usage cap in the Anthropic console for peace of mind.

### 5. File storage
- **Phase 1–4:** local filesystem under `./resumes/`
- **Phase 5+:** if deploying, move to S3 or Supabase Storage (servers don't have persistent local disk)

## End-to-end flow: "Add a job from URL"

1. User pastes a LinkedIn / job board URL into the dashboard form
2. Browser sends `POST /jobs {url: "..."}` to backend
3. Backend fetches the URL HTML (`requests.get`)
4. Backend sends the HTML + a structured-extraction prompt to Claude API
5. Claude returns JSON: `{title, company, level, yoe, must_have_skills, summary, ...}`
6. Backend validates JSON (Pydantic), inserts into `jobs` table
7. Backend asks Claude: "given these skills `[...]`, pick the best match from these resumes `[label1, label2, ...]`" → gets recommendation
8. Backend writes `recommended_resume_id` to the job row
9. Backend returns the job object to the frontend
10. Frontend (HTMX) swaps the new row into the jobs table — no page reload

## Hosting plan

| Layer | Phase 1–3 | Phase 4+ |
|---|---|---|
| Backend | localhost:8000 | Railway (or Render) free tier |
| DB | local SQLite file | Supabase Postgres free tier |
| Frontend | served by backend | same |
| Resumes | local `./resumes/` | Supabase Storage |
| Secrets | `.env` file (gitignored) | platform env vars |
| Domain | — | optional Cloudflare domain |

## Security & secrets (don't skip)

- **Never** commit API keys or `.env` to git. Add `.env` to `.gitignore` Day 1.
- Anthropic API key, DB URL, etc. live in `.env` locally, in platform env vars in prod.
- When deployed: add basic auth or a simple password page — this is your data, not the world's.

## Why this stack (vs alternatives)

| Choice | Why | What you'd pick instead, and why not |
|---|---|---|
| Python | Beginner-friendly, dominant in AI | JS/TS — fine but more concepts at once (build tools, async) |
| FastAPI | Modern, lightweight, great docs | Django — heavier, more conventions to learn before shipping |
| SQLite then Postgres | Free, simple, scales | MongoDB — fewer transferable SQL skills |
| HTMX | Ship UI in hours not weeks | React — great skill but 1–2 months on its own |
| Claude API | Already in the ecosystem; strong structured output | OpenAI — fine alt, but pick one and go |
| Railway | One-command deploys | AWS — power-user; rabbit hole for week 1 |

## Repo layout (proposed)

```
job-tracker/
├── CLAUDE.md             # project memory (this folder)
├── LEARNING.md           # tech roadmap
├── ARCHITECTURE.md       # this doc
├── README.md             # how to run it (for GitHub)
├── .gitignore
├── .env.example          # template, no real keys
├── pyproject.toml        # dependencies
├── tracker/              # the actual code
│   ├── __init__.py
│   ├── cli.py            # Phase 1 entry point
│   ├── db.py             # SQLite schema + queries
│   ├── extract.py        # Claude API calls
│   ├── models.py         # Pydantic schemas
│   └── api.py            # FastAPI app (Phase 3+)
├── resumes/              # gitignored
├── tracker.db            # gitignored
└── tests/
```
