# Job Tracker — Project Memory

> Living doc. Updated as we learn. Owned by: Ajinkya Kate. Started: 2026-05-23.

## 1. Why this project exists

Ajinkya is actively job-hunting. Today the process is messy: jobs come from LinkedIn posts, referrals, job boards. He reaches out to HRs/recruiters via DM or email, juggles multiple resume variants (PM, BA, Product Ops), and loses track of who he contacted, when, with what resume, and what came back.

The Job Tracker is **a personal command center** that owns the application lifecycle end-to-end — from "I saw a post" to "I got an offer / closed the loop." Built as a real product, but the user is one person (Ajinkya himself) first; if it's good, it generalizes later.

Secondary goal: **this is a learning vehicle**. Ajinkya is a PM with deep product instincts but limited hands-on coding. Building this teaches Python, APIs, AI integration, backend, frontend, hosting, and git/GitHub — all on a problem he cares about. See `LEARNING.md`.

## 2. Primary user persona — "The Active Seeker"

- Role: PM/BA-level professional, 2–5 yrs experience, transitioning between roles
- Volume: 10–30 applications/week across LinkedIn, job boards, referrals
- Lives in: LinkedIn feed, email, sometimes WhatsApp/Telegram for recruiter chats
- Tech comfort: high product literacy, moderate technical depth, prefers fast/clean tools over feature-heavy ones

### What hurts today
- **Memory loss** — "Did I already apply here? Who did I talk to? When was the last ping?"
- **Resume confusion** — sent the PM resume to a BA role by mistake; doesn't remember which version went where
- **Reading fatigue** — every JD is 500 words; needs the gist (role level, YoE, must-have skills) at a glance
- **Follow-up drift** — leads go cold because the user forgets to ping at the right interval
- **No funnel view** — can't see "5 awaiting reply, 3 interview-stage, 12 ghosted" in one screen

## 3. User stories (Phase 1 candidates)

Format: **[ID] As a seeker, I want X so that Y.**

- **US-1** Save a job posting by URL or paste, so I have one record of truth.
- **US-2** Auto-extract from a JD: role title, level, YoE, must-have skills, location, comp (if listed), so I don't read the whole post.
- **US-3** Store HR/recruiter contact (name, role, email, LinkedIn, phone) attached to a job, so I can follow up without hunting.
- **US-4** Track status per application: `Saved → Applied → Reached out → Replied → Interview → Offer/Rejected/Ghosted`, so I see where each lead is.
- **US-5** Get a follow-up reminder N days after my last activity, so leads don't go cold.
- **US-6** Upload multiple resume variants, tag each by role family (PM, BA, Product Ops), so I can pick the right one.
- **US-7** System recommends *which* resume variant fits a given JD based on skill overlap, so I stop agonizing.
- **US-8** Manually edit any auto-extracted field, because AI gets things wrong and I stay in control.
- **US-9** Dashboard view: open apps, awaiting reply, follow-ups due today, win-rate per resume variant.
- **US-10** Import a LinkedIn post URL → system extracts the job + the poster (HR/recruiter) as a contact in one shot.

### Stretch (later phases)
- Email integration — pull replies automatically
- Calendar sync for interviews
- Resume tailoring suggestions ("this JD wants X, your resume doesn't mention X")
- Multi-user / shareable (if friends want it)

## 4. Scope as session-sized "ships"

Work cadence is **flexible / no fixed schedule** (see [[project-job-tracker]] memory). The risk with that is stalling halfway through a big phase. So we structure work as **ships** — each ship ends in a working, demoable piece. Open the project, pick the next ship, finish it in 1–3 focused sessions, commit, close laptop. Next time, pick the next ship.

### Foundation
- **Ship 0 — Setup** — Python + venv + git init + GitHub repo + `.env.example`. Run a hello-world `tracker.py`. *(1 session)*

### Phase A — CLI core (no AI yet)
- **Ship 1 — JSON-backed CLI** — `tracker.py add` (manual entry: title/company/JD/status), `tracker.py list`. Saves to `jobs.json`. *(1–2 sessions)*
- **Ship 2 — SQLite swap** — same CLI, but `tracker.db` replaces JSON. Learn SQL. *(1 session)*
- **Ship 3 — Contacts** — `tracker.py contact add <job_id>`, tracks HR/recruiter. *(1 session)*
- **Ship 4 — Status + follow-ups** — status transitions, `tracker.py followups` shows due. *(1 session)*

### Phase B — AI does real work (heavy AI scope confirmed)
- **Ship 5 — JD extraction from pasted text** — `tracker.py add --paste`, opens editor, you paste the JD, Claude returns structured fields, you review and save. *(1–2 sessions)*
- **Ship 6 — JD extraction from URL** — `tracker.py add --url <url>`, try fetch, fall back to "paste this:" prompt if blocked (LinkedIn often blocks). *(1 session)*
- **Ship 7 — Resume registry** — `tracker.py resume add <file> --label "PM-senior" --tags pm,saas`. Multiple resumes. *(1 session)*
- **Ship 8 — AI resume recommendation** — `tracker.py recommend <job_id>` → Claude picks best resume for the JD with reasoning. *(1 session)*
- **Ship 9 — AI outreach drafts** — `tracker.py draft <job_id> <contact_id>` → Claude drafts a recruiter message tailored to JD + your resume. You edit before sending. *(2 sessions)*
- **Ship 10 — AI resume tailoring suggestions** — `tracker.py tailor <job_id> <resume_id>` → Claude suggests bullet-point tweaks to highlight what the JD wants. You apply manually. *(2 sessions)*

### Phase C — Web UI
- **Ship 11 — FastAPI on top of the CLI** — same functions, exposed as HTTP. `/docs` UI works. *(2 sessions)*
- **Ship 12 — HTMX dashboard** — jobs table, status badges, follow-ups-due panel. *(2 sessions)*
- **Ship 13 — Add-job form + edit modals** — paste/URL input on the web. *(2 sessions)*

### Phase D — Cloud
- **Ship 14 — Migrate to Supabase Postgres** — same schema, different DB. *(1 session)*
- **Ship 15 — Deploy backend to Railway** — live URL, env vars, basic auth. *(2 sessions)*
- **Ship 16 — Email follow-up reminders** — daily cron, email digest. *(2 sessions)*

**Total: ~25 sessions.** No fixed timeline; success = a working ship every time you open the project.

## 5. Out of scope (deliberately)

- Multi-user SaaS — single user (Ajinkya) is the entire customer for v1
- Browser extensions / scraping at scale — fragile, legally murky
- Auto-applying to jobs — ethically risky and recruiters hate it
- Mobile app — web responsive is enough
- AI that writes cover letters end-to-end without review — keeps the user in the loop

## 6. Draft data model

```
jobs
  id, title, company, jd_url, jd_raw_text, jd_summary,
  level (junior/mid/senior), yoe_required, must_have_skills (list),
  nice_to_have_skills (list), location, comp_range,
  source (linkedin/board/referral), date_saved, status,
  applied_resume_id (FK), recommended_resume_id (FK), notes

contacts
  id, job_id (FK), name, role (HR/hiring_mgr/referral),
  email, linkedin_url, phone, last_followup_date, next_followup_date, notes

resumes
  id, label (e.g., "PM-senior-v3"), file_path, role_family,
  skill_tags (list), last_updated, win_count, loss_count

events
  id, job_id (FK), type (saved/applied/reached_out/replied/interview/offer/rejected),
  date, channel (email/linkedin/call), note
```

## 7. Definition of Done — Phase A (CLI core)

- [ ] Repo on GitHub with README
- [ ] `tracker.py add` (manual) works
- [ ] `tracker.py list` works with filters
- [ ] `tracker.py contact add` works
- [ ] `tracker.py status` + `tracker.py followups` work
- [ ] Used by Ajinkya for at least 10 real job applications before moving to Phase B

## 8a. How we work — two modes

This project runs in two persona-driven operating modes, each living in its own folder so the project is self-documenting after any gap:

- **Business mode** — `business/` folder. Persona: **Forward Deployed Engineer (FDE)** (`business/persona_fde.md`). Used for product thinking, requirement gathering, scoping, validation, PM-interview prep. Output: `business/requirements_v*.md` (questions asked AND answers given are both logged — process is part of the artifact).
- **Tech mode** — `tech/` folder. Persona: **Patient Teacher** (`tech/persona_teacher.md`). Used for learning concepts (every "what is X?" gets a lesson file in `tech/lessons/`) and building actual code in `tech/code/`. Each lesson ends with a 60-second interview-ready answer.

When in doubt about which mode is active, ask. The personas are not interchangeable — the FDE doesn't write Python; the teacher doesn't gather requirements. PM interview prep flows through business mode. Tech interview prep flows through tech mode.

**Gate:** don't enter tech mode (start Ship 0) until `business/requirements_v1.md` has enough confidence — pain, workarounds, and success criteria all gathered, scope re-validated.

## 8. Decisions made (2026-05-23)

- **Input mode**: both URL fetch and paste fallback (LinkedIn often blocks bots, so paste is the reliable path)
- **AI scope**: heavy — extraction *and* outreach drafts *and* resume tailoring suggestions *and* resume-pick recommendation. User reviews everything before it leaves the tool.
- **First form factor**: CLI (Phase A) — defer web UI to Phase C
- **Cadence**: flexible — work is shaped into "ships" so each session ends with something working
- **AI provider**: Anthropic Claude (already in the ecosystem; strong structured output)
- **Frontend later**: HTMX (not React)
- **Hosting later**: Railway + Supabase free tiers
