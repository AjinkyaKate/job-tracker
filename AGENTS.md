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

## 4. Scope as session-sized "ships" — REVISED 2026-05-24 after Session 7

> Original 16-ship plan was set during scope freeze. After 4 ships shipped and 3 new user asks (resume engine, persona analysis, JD/company analysis), revised to a tighter MVP-deploy path with a clearly-separated Phase 2.

### ✅ Phase 1 (Sprint 1) — CLI tracker — DONE
- **Ship 0** ✅ (commits `293dc9a` + `892e846`) — project skeleton, Python + venv + git + GitHub + first hello-world
- **Ship 1** ✅ (commit `8c1a8ff`) — JSON-backed CLI: `add` + `list`
- **Ship 2** ✅ (commit `aa33565`) — SQLite swap; `jobs.json` → `tracker.db`
- **Ship 3** ✅ (commit `e5ea8e5`) — contacts table + multi-contact per job + `contact` command
- **Ship 4** ✅ (commit `b63a69c`) — status transitions + events table + `next_action_at` + `today` view + `show <job>` + `pursue` + `event` + `status` + `action` commands

**Outcome:** "Never Lose a Thread" anchor delivered in CLI form. Real job leads live in the local DB.

### 🟡 Sprint 2 — MVP Web Deployed (in progress)

- **Ship 6 — FastAPI web dashboard** (current ship; multi-phase)
  - Phase A: install FastAPI + first homepage route showing today + jobs (this turn)
  - Phase B: job detail page (`/jobs/{id}`) + add-job form
  - Phase C: HTMX for status updates / next-action edits without page reload
  - Phase D: status-column "kanban" view with drag-to-change-status (HTMX, no real JS)
- **Ship 7 — Deploy**
  - Migrate SQLite → Supabase Postgres (data + schema)
  - Deploy backend to Railway (`*.up.railway.app` URL)
  - Phone-accessible. Add HTTP basic auth so it's not world-readable.

**Sprint 2 goal: a real URL opens on the phone showing today's call-prep card, lets the user mark status as they go, and add new leads.**

### ⏭ Sprint 3 — AI ingestion (Ship 5)

Slot in AFTER Ship 6 is on localhost (so AI features land in the UI right away).

- **Ship 5 — Anthropic API integration**
  - Requires user-provided API key (`.env`-managed; never committed)
  - Paste any text (LinkedIn post / email thread / JD) → Codex returns structured fields → user reviews → saves to DB
  - Endpoint `POST /extract` in the web app
  - Lessons 09 (HTTP/APIs) + 10 (LLM APIs) land here

### ⏭ Phase 3 — Gmail integration for LinkedIn event auto-detection (NEW from Session 9)

**Why:** LinkedIn doesn't expose an API for messages/connections/applications. But LinkedIn *emails* the user about every event — connection accepted, message received, InMail received, application viewed, profile viewed. We read those Gmail messages via Google's Gmail API, parse them, and auto-log events into the tracker.

**Why this is the safest path (vs scraping):** Doesn't violate LinkedIn TOS, doesn't risk Ajinkya's LinkedIn account (which is critical during job hunt). Uses official Google OAuth.

**Ship breakdown (3 turns total):**

- **Phase 3 ship 1/3 — Scaffolding + setup doc** (this turn): roadmap entry, `GMAIL_SETUP.md` with Google Cloud Console step-by-step, `oauth_tokens` schema table, stub `gmail_integration.py` module, stub OAuth routes in webapp.py, Google API libs added to requirements.txt
- **Phase 3 ship 2/3 — Real OAuth flow + credential storage** (next turn, after user completes Google Cloud setup): `/auth/gmail/start` redirects to Google consent → `/auth/gmail/callback` stores access + refresh tokens. Test: user grants access, we have a working creds row in oauth_tokens.
- **Phase 3 ship 3/3 — Email parser + sync engine** (turn after): parse common LinkedIn email patterns (subject regex + sender filter), fuzzy-match person names to existing contacts in tracker.db, log events. Manual "Sync Now" button + automatic on-page-load sync.

**Events we'll auto-detect:**
| LinkedIn email pattern | Maps to event_type |
|---|---|
| `"X accepted your invitation"` | `connection_accepted` (status_change Saved → Reached-out if applicable) |
| `"New message from X"` | `message_received` |
| `"X sent you a message"` | `message_received` |
| `"InMail from X"` | `inmail_received` |
| `"Your application was sent to Y"` | `application_sent` |
| `"X is interested in your application"` | `interview_invited` or `recruiter_interest` |
| `"X viewed your application"` | `application_viewed` |

**Out of scope (deferred):**
- Gmail push notifications via Cloud Pub/Sub (more setup) — use polling/manual sync for v1
- Reading Gmail messages outside LinkedIn senders — scope creep
- Replying to emails from the app — adds complexity

### ⏭ Phase 4 — Notifications (NEW from Session 10)

**Why:** Once Phase 3 is auto-detecting LinkedIn events from Gmail, the user shouldn't have to refresh the dashboard to know something happened. Notifications surface new events in real-time.

**Ship breakdown:**
- **In-app toast** when dashboard is open and Gmail sync logs a new event. Already have the toast component from Phase B kanban; just wire it to render new events fetched on a polling interval (every 60s) or on Gmail-sync-complete.
- **Browser Web Notifications API** — for background tabs / when dashboard isn't focused. Requires user permission (one-time). Fires on connection_accepted / message_received / interview_invited etc. Quiet hours configurable.
- **Daily / weekly email digest** (optional) — Cron-triggered: every morning, send a summary email of "yesterday's activity" to the user's own Gmail. Helps surface trends + going-cold leads.

**Depends on:** Phase 3 (Gmail sync) being live first — without auto-detection, there's nothing to notify about.

**Tech:**
- Polling: client-side `setInterval(() => fetch('/events/since?ts=...'), 60_000)`
- Web Notifications: `Notification.requestPermission()` + `new Notification(title, {body, icon})`
- Email digest: Python `smtplib` or transactional service (Resend/Postmark free tier)

### 🔭 Phase 2 — Post-deploy iterations (NEW asks from Session 7)

After MVP is deployed and AI ingestion is live, layer these:

- **Phase 2a — Resume engine**
  - `resumes` table: store multiple variants (PM, BA, Product Ops) with markdown body + skill tags
  - `tracker.py resume add` + web UI for resume management
  - Per-job tagging: which resume was sent

- **Phase 2b — JD analysis brain**
  - For each job, AI extracts: must-have skills, nice-to-haves, YoE required, level, comp signal, hiring urgency signal (recently posted? actively reposted?)
  - Auto-classify `worth_pursuing` based on user's profile vs JD requirements

- **Phase 2c — Persona analysis brain**
  - For a given LinkedIn profile (paste text), AI extracts: role, seniority, mutual connections, signal for warm-DM-vs-formal-tone

- **Phase 2d — Company analysis brain**
  - Paste a company page or URL, AI returns: what they do, recent news, funding stage, glassdoor sentiment (if pasted), competitor positioning

- **Phase 2e — AI resume tailoring**
  - Given a job + chosen resume variant, AI suggests bullet-level edits to highlight the JD's keywords
  - User reviews and applies (or rejects) each suggestion. Never auto-changes.

- **Phase 2f — AI outreach drafts**
  - For each contact + their conversation thread (events), AI drafts a polite next message
  - User reviews/edits/sends. Never auto-sends.

### ❌ Won't have (still out of scope)

- Multi-user / SaaS — single-user (Ajinkya) is the entire v1 customer
- Auto-applying to jobs — reputational risk
- Mobile native app — web-responsive is enough
- LinkedIn scraping at scale — fragile and ToS-murky; paste-mode covers the use case

Cadence is flexible / no fixed schedule. Each ship still ends in a working, demoable piece — open, pick the next ship, finish it in 1–3 focused sessions, commit, push.

> Earlier 16-ship plan (Phases A–D) is superseded by this revised plan. Old commits referenced the old numbering; new commits use this scheme.

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
- **AI provider**: Anthropic Codex (already in the ecosystem; strong structured output)
- **Frontend later**: HTMX (not React)
- **Hosting later**: Railway + Supabase free tiers
