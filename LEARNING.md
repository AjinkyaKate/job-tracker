# Tech Learning Roadmap

Goal: build the Job Tracker end-to-end *and* come out fluent in: Python, APIs, AI integration, web backend, basic frontend, deployment, git/GitHub.

Style: **learn by building**. Each phase teaches one concept and produces a working piece of the tracker. No "tutorial hell." If you can't explain it after a phase, redo the build.

---

## Phase 1 — Python fundamentals (Week 1, ~6–8 hrs)

**What to learn**
- Variables, types (str, int, list, dict), functions, conditionals, loops
- File I/O — reading/writing text and JSON
- Running a `.py` file from the terminal
- Virtual environments (`python -m venv`) and `pip install`

**Mini-build:** a script `tracker.py` that:
- Reads `jobs.json` (a hand-edited file of fake jobs)
- Prints them as a table
- Takes a CLI arg to filter by status

**Resources (pick one, don't churn)**
- Automate the Boring Stuff with Python (free online)
- Or: Corey Schafer's YouTube Python series (faster)

**Check-yourself test:** can you, without looking, write a function that loads a JSON file, filters a list of dicts by a field, and returns the result?

---

## Phase 2 — APIs & HTTP (Week 2, ~4–6 hrs)

**What to learn**
- What an HTTP request is (GET, POST, headers, body, status codes)
- The `requests` library
- Reading API documentation (Anthropic's docs are a good model)
- API keys, secrets, env vars (`.env` + `python-dotenv`)

**Mini-build:** fetch a public job posting URL (or LinkedIn post HTML), save it to a file.

**Check-yourself test:** explain to yourself what happens between "I paste a URL" and "I see HTML in my script."

---

## Phase 3 — AI integration (Week 2–3, ~6 hrs)

**What to learn**
- What an LLM is, what a prompt is, what tokens are
- Anthropic Claude API — `anthropic` Python SDK
- Asking for **structured JSON output** (this is the magic for our extractor)
- Prompt design: clear instructions, examples, fallback for missing fields

**Mini-build:** feed a JD into Claude → get back JSON with `{title, company, level, yoe, must_have_skills, summary}`. Pretty-print it.

**Skill cap unlocked:** AI as a backend primitive, not a chat toy.

**Note:** when working in this repo with Claude Code, ask Claude to use its `claude-api` skill for guidance on caching, model choice, structured output patterns.

---

## Phase 4 — Databases (Week 3, ~4 hrs)

**What to learn**
- SQL basics: CREATE TABLE, INSERT, SELECT, UPDATE, DELETE, JOIN
- SQLite — zero-config, one-file DB
- Python's built-in `sqlite3` module
- Schema migrations (rename later: just rewrite for now)

**Mini-build:** replace the `jobs.json` file with `tracker.db`. All Phase 1 operations now hit SQLite.

**Check-yourself test:** write a query that returns all jobs in status "Applied" with a follow-up due in the next 3 days.

---

## Phase 5 — Web backend (Week 4, ~8 hrs)

**What to learn**
- What a server is (long-running process that listens on a port)
- Request/response cycle, JSON API design
- FastAPI: routes, path/query/body params, Pydantic models
- Auto-generated API docs (`/docs` endpoint — gold for learning)

**Mini-build:** expose tracker via HTTP:
- `POST /jobs` (body: URL) → extracts and saves
- `GET /jobs` → returns list
- `PATCH /jobs/{id}/status` → updates status
- `POST /contacts` → adds HR contact

**Check-yourself test:** hit your own endpoints from `curl` and from the browser's `/docs` UI.

---

## Phase 6 — Frontend (Week 5, ~8 hrs)

**What to learn**
- HTML structure (forms, tables, semantic tags)
- Basic CSS (Tailwind via CDN to skip styling fights)
- **HTMX** — sprinkle interactivity into HTML without writing JS
- (Optional later: React if you want to learn it as a separate exercise)

**Mini-build:**
- Dashboard page: table of jobs, status badges, "follow up due" indicator
- "Add job" form: paste URL → page updates with extracted data
- Contact panel per job

**Why HTMX over React (for now):** React is a 3-month detour. HTMX gives you a working UI in days. As a PM, you want to *ship*, not become a frontend engineer.

---

## Phase 7 — Git & GitHub (start Day 1, continuous)

**What to learn**
- `git init`, `add`, `commit`, `push`
- Branches: `git checkout -b feature/x`
- GitHub repos, READMEs, `.gitignore`
- (Later) pull requests — even solo, useful for self-review

**Mini-build:** this entire project lives in a GitHub repo from commit #1. README explains what it does.

---

## Phase 8 — Deployment (Week 6, ~6 hrs)

**What to learn**
- What "deploying" means (your code, running on someone else's computer, reachable via URL)
- Railway or Render (free tiers, dead simple)
- Environment variables in production (API keys, DB URL)
- Supabase: managed Postgres + free tier — migrate from SQLite

**Mini-build:** the Job Tracker is live at a URL you can share. You can add a job from your phone.

---

## Tools & accounts to set up Day 1

- [ ] VS Code (editor)
- [ ] iTerm2 (nicer terminal) — optional
- [ ] Python 3.11+ installed (`brew install python@3.11`)
- [ ] GitHub account
- [ ] Anthropic API account ($5 credit to start is plenty)
- [ ] Railway account (free tier, deploy later)

## How to learn efficiently as a PM

- **One concept per session.** Don't try to learn Python *and* SQL *and* FastAPI in one day.
- **Build > consume.** 30 min of tutorial then 60 min of hacking on your code. Not 4 hrs of tutorials.
- **Use Claude Code as a pair-programmer**, but ask it to *explain*, not just spit code. "Why did you choose X here?" "Walk me through this line."
- **Commit daily.** Even one line. Streaks build habit.
- **Ship Phase 1 ugly.** It can be a CLI with no styling. Polish later.

## Estimated total time
- Phase 1–4 (CLI + AI + DB): ~24 hrs
- Phase 5–6 (backend + UI): ~16 hrs
- Phase 7–8 (git + deploy): ~10 hrs spread throughout
- AI features at the heavier end of scope (outreach drafts, resume tailoring): +10 hrs
- **Total: ~60 hrs.** No fixed wall-clock estimate — see ship-based plan in `CLAUDE.md`.

## Cadence note — flexible / no fixed schedule

You picked "no fixed cadence." The honest tradeoff: this maximizes flexibility but is the #1 reason side projects die. Mitigation built into the plan:

- **Ship-based scope** (see `CLAUDE.md` §4). Every ship is 1–3 sessions and ends with working code. You should never close the laptop mid-ship — pick small ships if you only have an hour.
- **Commit at the end of every session.** Even a half-finished ship gets a WIP commit. GitHub streaks help.
- **Re-read this folder's `CLAUDE.md` when you come back.** It's the memory across gaps. If you've been away 2 weeks, spend 10 min re-reading before coding.
- **Anchor: pick the next ship at the start of each session, before opening the editor.** No "what was I doing?" minutes.

## A note on the heavy-AI scope

You picked the ambitious AI path (extraction + outreach drafts + resume tailoring). Two implications:

- **Prompt engineering becomes a real skill** to learn. Budget time to iterate on prompts — the first version always sucks. Use Claude Code's `claude-api` skill for guidance on structured output, examples, fallback patterns.
- **The "review before send" rule is non-negotiable.** AI-drafted outreach that goes out unread will burn bridges with recruiters. Build the UX so editing is the default path, sending is an explicit click.
