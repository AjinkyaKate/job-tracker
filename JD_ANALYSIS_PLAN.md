# JD Analysis — Feature Spec

Status: DRAFT, awaiting Ajinkya approval
Date: 2026-05-26


## Goal

When a lead lands in `/leads`, I don't want to read the full JD text. I want the AI to tell me three things at a glance:
1. What skills does this role want
2. Is there an HR email I can use to skip the job-board funnel
3. Should I apply or skip, based on my profile

This replaces "open JD, read 2000 words, decide" with "look at badge, decide, click for detail if needed".


## User stories

1. As Ajinkya, when I land on `/leads` I see a STRONG / MAYBE / SKIP badge on each already-analyzed card so I can triage 50 cards in under a minute.
2. When I expand a card I see the full breakdown: required skills, HR email if found, 2-3 sentence summary, and one-line reason for the score.
3. I click "Analyze this JD" on cards that haven't been analyzed yet. Result caches in the DB so I never pay for the same analysis twice.
4. I can edit my profile at `/profile` so the score matches my actual goals over time.


## UX flow

**Path 1 — first time on a card:**
1. I expand a lead card.
2. The expanded section has a new "Analyze this JD" button at the top.
3. I click it. Spinner shows for 2-5 seconds.
4. AI result fills in: score badge, skills chips, HR email if any, summary, reason.
5. The collapsed card header now also shows the score badge.
6. Result saved to DB. Future page loads show the analysis instantly.

**Path 2 — return to an already-analyzed card:**
1. I land on `/leads`.
2. All previously-analyzed cards show their score badge in the collapsed view.
3. I scan badges. Expand only the STRONG ones to read details.
4. Un-analyzed cards still have the "Analyze" button.

**Path 3 — editing my profile:**
1. I open `/profile`.
2. I see a textarea pre-filled with my current profile (seeded on first visit).
3. I edit freely, click Save.
4. Future analyses use the updated profile.
5. Already-analyzed cards keep their old score until I manually click "Re-analyze".


## Wireframes (text)

### Collapsed lead card with score badge
```
┌─────────────────────────────────────────────────────────┐
│ [PT]  Senior Product Manager · Razorpay · Bengaluru     │
│       added 2h ago · #234 · ✓ JD fetched   [STRONG]  ⌄ │
└─────────────────────────────────────────────────────────┘
```
Badge colours: green (STRONG), amber (MAYBE), red (SKIP).
Cards without analysis: no badge, "Analyze" button visible in expanded view only.

### Expanded card with full analysis
```
┌─────────────────────────────────────────────────────────┐
│ Senior Product Manager · Razorpay                       │
│ Bengaluru · added 2h ago · ✓ JD fetched                 │
├─────────────────────────────────────────────────────────┤
│ [STRONG]  Strong match: B2B SaaS + AI features map      │
│           directly to your D·engage work.               │
│                                                          │
│ Required skills:                                        │
│  [Product Management] [LLM features] [B2B SaaS]         │
│  [Customer Discovery] [Stakeholder Mgmt]                │
│                                                          │
│ HR contact: arun.s@razorpay.com                         │
│                                                          │
│ Summary:                                                │
│ Senior PM owning AI-powered onboarding for Razorpay's   │
│ business-banking suite. 5+ yrs ideal, exposure to       │
│ payments rails preferred.                               │
│                                                          │
│ [Re-analyze]                                            │
│                                                          │
│ Show full JD ↓     [📄 Resume]                          │
│ [🔗 Open & apply]  [✓ I Applied]  [✕ Remove]            │
└─────────────────────────────────────────────────────────┘
```

### Profile page (`/profile`)
```
┌─────────────────────────────────────────────────────────┐
│ My Profile                                              │
│                                                          │
│ This is what the AI uses to score job descriptions.    │
│ Be specific. The more accurate this is, the better the │
│ matches.                                                │
│                                                          │
│ ┌─────────────────────────────────────────────────────┐│
│ │ Product Owner at D·engage (B2B SaaS, ~2 yrs).       ││
│ │                                                      ││
│ │ Customer-facing work: integration coordination,     ││
│ │ release management, vendor partner liaison.         ││
│ │                                                      ││
│ │ Strong with AI tools (Claude, Gemini), B2B SaaS,    ││
│ │ enterprise integrations. CSPO certified.            ││
│ │                                                      ││
│ │ Looking for: PM, PO, Customer Engineer, Solutions   ││
│ │ Engineer, Vibe Coding Engineer roles.               ││
│ │                                                      ││
│ │ Open to: Mumbai, Pune, Bengaluru, remote India.     ││
│ │ Available immediately.                              ││
│ └─────────────────────────────────────────────────────┘│
│                                                          │
│  [Save profile]                                         │
└─────────────────────────────────────────────────────────┘
```


## Data model changes

### Columns added to `jobs` table:
- `ai_score` TEXT  (one of STRONG / MAYBE / SKIP, or NULL if not yet analyzed)
- `ai_score_reason` TEXT  (one-sentence reason, max ~30 words)
- `ai_required_skills` TEXT  (comma-separated, max 8 skills)
- `ai_hr_email` TEXT  (extracted from JD if present, else NULL)
- `ai_jd_summary` TEXT  (2-3 sentence summary)
- `ai_analyzed_at` TEXT  (ISO timestamp, used for cache invalidation)

### New table `user_profile`:
```sql
CREATE TABLE user_profile (
    user_id INTEGER PRIMARY KEY,
    profile_text TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```
Seeded on first `/profile` visit with a default profile if the user has none.

Migrations are idempotent via `column_exists()` (same pattern as the multi-tenant migration).


## AI prompt (Gemini)

System: structured JSON response using Gemini's response_schema.

```
You're analyzing a job description for a candidate.

Return JSON with:
- score: one of "STRONG", "MAYBE", "SKIP"
- score_reason: one sentence why, max 25 words
- required_skills: list of 5-8 top skills from the JD
- hr_email: email from the JD if mentioned, else null
- summary: 2-3 sentence plain summary of the role

Scoring rubric:
- STRONG: profile matches the core asks of the role AND no hard blockers (years gap of more than 3, missing domain, wrong location, wrong work-mode)
- MAYBE: profile matches roughly half the asks, OR strong matches but with one stretchy gap (years short by 1-2, learnable domain, etc.)
- SKIP: hard mismatch on years (gap > 4), domain, or any explicit must-have the profile can't claim

# Candidate Profile
{profile_text}

# Job Description
Title: {title}
Company: {company}
Location: {location}

{jd_raw_text_truncated_to_10000_chars}

Return only the JSON. No markdown, no preamble.
```


## Implementation phases

### Phase 1 — Data + AI plumbing (2-3 hrs)
- Add `ai_*` columns to `jobs` table via idempotent migration in `db.init_schema()`
- Add `user_profile` table
- New module `jd_analyzer.py` exposing `analyze_jd(conn, job_id, user_id, force=False) -> dict`
- Caching: if `ai_analyzed_at` is set and `force=False`, return cached row
- Local test: invoke from Python REPL on 3 existing leads

### Phase 2 — Profile page (1-2 hrs)
- Routes: `GET /profile` (render form) and `POST /profile` (save)
- Template: `templates/profile.html`
- On first visit, seed with default Ajinkya profile text
- Nav link in `base.html` so it's reachable

### Phase 3 — Analyze button + cached display (2-3 hrs)
- New route: `POST /jobs/{id}/analyze`
- Modify `templates/leads.html`: each expanded card gets the button + AJAX call
- Spinner during call, result appears inline on success
- Display: badge + reason + skills chips + HR email + summary
- Re-analyze button visible after first analysis (uses `force=True`)

### Phase 4 — Score badge in collapsed view (1 hr)
- Modify the compact card header in `leads.html`
- Read `jobs.ai_score`, render coloured badge if not NULL
- Badge colours via existing design tokens (green/amber/red)

### Phase 5 — End-to-end test + production deploy (1 hr)
- Local test on 5 different JD types (PM, CSE, Founding, Ops, Engineer)
- Verify score reasoning is sensible across all 5
- Push to prod, smoke test on Render URL
- Verify migration runs cleanly on prod Postgres


## Testing checklist

### Local sanity
- [ ] Analyze on rich JD → sensible STRONG / MAYBE / SKIP with reason
- [ ] Analyze on JD with HR email → email extracted to `ai_hr_email`
- [ ] Analyze on JD without HR email → `ai_hr_email` is NULL, no crash
- [ ] Re-analyze overrides cached result
- [ ] Profile save survives page reload
- [ ] Profile edit reflects in next analysis (not auto-rerun on existing)
- [ ] Badge colour matches score in collapsed view

### Edge cases
- [ ] Gemini quota exhausted → graceful error message, no crash
- [ ] JD > 10K chars → truncate before sending to Gemini
- [ ] Empty profile → fall back to default profile, log warning
- [ ] Job has no `jd_raw_text` → button shows "JD not fetched yet" instead of running

### Production
- [ ] DB migration runs clean on Render Postgres without breaking existing data
- [ ] Analyze button works end-to-end on prod URL
- [ ] No leaked secrets in logs


## Out of scope for v1

- Auto-running analysis on every new lead during Gmail sync (cost concern, deferred per your decision)
- Multi-LLM provider switch (still Gemini only; Claude/OpenAI is task #90)
- Skill match heatmap (vs. simple chip list)
- Profile versioning / history
- Re-analyzing all leads when profile changes (manual per-card only)
- Bulk operations ("analyze all visible cards")
- Score history / score-change tracking
- Export analysis as PDF
- Notifications when a new STRONG lead arrives


## Estimated total build: 8-11 hours

Spread over 1-2 working sessions. Phase 1 + 2 is one session, Phases 3-5 the next.


---
## Approval gate

Please review and reply with one of:
- "Approved, build it"
- "Change X" (and I'll revise this doc, no code yet)
- "Approved with these changes: ..." (I'll start Phase 1)
