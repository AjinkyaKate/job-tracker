# LinkedIn alerts → Job Tracker leads inbox

Once-only setup. ~5 minutes in your LinkedIn account. After this, every morning your `/leads` page shows new postings matching your saved searches — no manual browsing required.

## How the flow works

```
LinkedIn saved search  →  daily email to your Gmail
                        ↓
       Gmail sync (every 10 min via GitHub Actions)
                        ↓
       linkedin_alerts.parse_alert() extracts each job
                        ↓
       INSERT into jobs table with status='lead'
                        ↓
       Visible at /leads — triage with [Pursue] / [Dismiss]
```

Pursue → moves to `status=saved` (kanban Saved column). Then you click the LinkedIn URL on the job page → read full JD → apply externally → confirmation email → Gmail sync auto-advances status to `applied`.

## Step 1 — Set up saved-search alerts on LinkedIn

Go to https://www.linkedin.com/jobs/search/

For each role you want to track, do this:

1. Search the title + location combination (e.g. "Product Owner" + "Pune District")
2. Apply work-mode filters (Hybrid / Remote / On-site as you prefer)
3. Click the **"Set alert"** toggle at the top of results
4. Frequency: **Daily via email and notification**

## Step 2 — Recommended alerts for Ajinkya's profile

Replace your current 8 alerts with these 8 better-targeted ones:

| Search title | Location | Filters | Why |
|---|---|---|---|
| Product Owner | Pune District, Maharashtra, India | On-site · Hybrid · Remote | YOUR EXACT CURRENT TITLE — top priority |
| Product Owner | Mumbai Metropolitan Region | On-site · Hybrid · Remote | PO-titled Mumbai fallback |
| Product Manager | Pune District, Maharashtra, India | On-site · Hybrid · Remote | Broader PM search in your city |
| Associate Product Manager | Pune District, Maharashtra, India | On-site · Hybrid · Remote | APM Pune-local |
| Associate Product Manager | Mumbai Metropolitan Region | On-site · Hybrid · Remote | APM Mumbai |
| Senior Product Manager | Pune District, Maharashtra, India | Hybrid · Remote | Level-up aspiration |
| Product Manager | India | Remote | Catches India-Remote jobs (skips US Remote noise) |
| Business Analyst | Pune District, Maharashtra, India | On-site · Hybrid · Remote | Adjacent role family — fallback |

**Delete these from your current alerts:**

- Worldwide alerts (too broad — 100s of irrelevant emails/day)
- US Remote alerts (rarely hires India-based, brutal time zones)
- "email marketing specialist" (different role family — adds noise)

## Step 3 — Wait

First alerts land within 24 hours. They arrive in two formats:

1. **Digest** — "10 new jobs for `<search-term>`" — list of multiple jobs
2. **Featured** — `"<job title> at <company>"` — one primary + several related

The parser handles both formats. Every listed job inserts as a lead in your tracker.

## Step 4 — Daily triage

Open https://job-tracker-bmhy.onrender.com/leads each morning. Spend ~5-10 min:

- **Pursue** — for jobs worth applying to. Status moves to `saved`, opens the LinkedIn URL. You read full JD → apply via LinkedIn → confirmation email lands → status auto-advances to `applied`.
- **Dismiss** — for jobs that are clearly wrong (off-domain, wrong level, etc.). LinkedIn won't re-import dismissed jobs (dedup by URL).

## Troubleshooting

**No leads showing up after 24 hours.**

1. Verify Gmail sync is running: https://github.com/AjinkyaKate/job-tracker/actions → check "Gmail autosync" workflow runs
2. Check that LinkedIn is actually emailing you (open Gmail → search `from:jobalerts-noreply@linkedin.com`)
3. Trigger a manual sync: `curl -X POST -u ajinkya:<password> https://job-tracker-bmhy.onrender.com/gmail/sync`
4. Look at the response — `leads_ingested` field should be > 0

**Same job showing up multiple times in leads.**

Shouldn't happen — dedup is on the canonical LinkedIn URL. If it does, paste the duplicated leads back to me with their IDs and I'll fix the parser.

**LinkedIn changed their email format and parsing broke.**

Push me a fresh sample of one of the new-format emails. Parser is regex-based, easy to update.

## What's NOT in Phase 1 (coming next)

- **AI fit-scoring** — Gemini rates each lead 0-100 against your profile + preferences, surfaces only high-fit ones
- **Auto-tailor resume on Pursue** — when you promote a lead, the resume generation kicks off in background so it's ready when you open the job page
- **Warm-contact cross-reference** — import your LinkedIn connections CSV, surface anyone in your network at the lead's company
