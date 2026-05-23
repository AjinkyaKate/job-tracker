# Lesson 08 — State, transitions, and event logs

> Triggered by: Ship 4 (status transitions + events table + today view). Time to read: ~8 min.

## In one sentence

A **status field** tells you *where* something is right now; an **event log** tells you *how it got there*. Together they answer both "what's the current state?" and "what's happened over time?"

## A real-world analogy — a package tracker

When you ship a package, you see two things on the carrier's tracking page:

- **The current status** at the top: "Out for delivery."
- **The history** below: "Tuesday 9 AM — picked up. Wednesday — in transit. Thursday 8 AM — out for delivery."

The status is *mutable*: it changes every few hours. The history is *append-only*: nothing is ever erased; every scan adds one more line. Together they tell the full story.

Your job tracker needs both for the same reason. The status answers *"where's Presolv360 right now?"* (awaiting_hr_review). The event log answers *"how did we get here? What did I do, when, and what did they say back?"* That history is what makes a follow-up call effective — you walk in knowing the timeline cold.

## Where this shows up in our project

Ship 4 adds:

- **New columns on `jobs`** — `next_action_at`, `next_action_note`, `worth_pursuing`, `last_activity_at`
- **New `events` table** — append-only log of everything that's happened on a job

So for Presolv360 (Job #1), the data shape becomes:

```
JOB #1
  status            = "awaiting_hr_review"      (mutable)
  next_action_at    = "2026-05-25"              (mutable)
  next_action_note  = "Call Latika +91-..."     (mutable)
  worth_pursuing    = "yes"                     (mutable)
  last_activity_at  = "2026-05-23T18:38:00"    (mutable)

EVENTS (append-only, oldest to newest):
  e1  2026-05-23 14:51  message_sent     "Hi Krunal" (DM)
  e2  2026-05-23 17:21  message_received "reach out to Latika..."
  e3  2026-05-23 17:27  email_sent       "Krunal Modi suggested..."
  e4  2026-05-23 18:38  email_received   "will review and get back..."
  e5  2026-05-25 ??     [your call goes here once it happens]
```

You can mutate the status however you want; the events row never changes.

## The minimum you need to know

### 1. Status = state machine

Your job moves through a defined set of states. For our tracker, roughly:

```
   Saved → Applied → (Replied | Rejected | Ghosted)
           Replied → Interview
           Interview → (Offer | Rejected)
           ANY → Backlog                          (parked, not pursuing now)
           ANY → Withdrawn                        (you stopped)
```

We don't *enforce* valid transitions in code yet — any string status is allowed. As we hit invalid moves we'll add validation. Real-world state machines often have a separate "allowed transitions" table; that's overkill for v1.

### 2. Why we need both status AND events

| Approach | Pros | Cons |
|---|---|---|
| **Status only** | Fast to query "current state" | No history. Can't answer "when did I apply?" or "what was the message we sent?" |
| **Events only** ("event sourcing") | Perfect audit trail. State derivable by replaying | Slow to ask "show me all jobs in `applied` status" — you'd have to replay every event for every job |
| **Both** (what we're doing) | Fast lookups + full history. Status is computed from events at write-time, not read-time | Slight duplication — status could in theory disagree with the latest event |

The "both" pattern is the practical middle ground for almost every app. Pure event sourcing is a thing in some domains (banking, audit-heavy systems); not needed here.

### 3. `occurred_at` vs `recorded_at` — two timestamps

Notice the `events` table has two timestamps:

- **`occurred_at`** — when the thing *actually happened* (e.g., the email was sent at 5:27 PM)
- **`recorded_at`** — when *you logged it into the tracker* (might be days later if you're catching up)

This separation matters for **backfilling**. Today is Saturday; you can record on Saturday that an email was sent Thursday. The chronology of *what happened* stays accurate even when you log late. Most CRMs and audit systems have this two-timestamp pattern.

### 4. The new CLI commands

| Command | What it does |
|---|---|
| `tracker.py status <job_id> <new_status>` | Updates `jobs.status` + appends a `status_change` event |
| `tracker.py action <job_id> <YYYY-MM-DD> "<note>"` | Sets `next_action_at` and `next_action_note` |
| `tracker.py event <job_id> <event_type> "<body>"` | Logs any kind of event manually |
| `tracker.py today` | Shows jobs with action due today/overdue + upcoming + status counts |

### 5. Common event types

We don't define an enum in the schema (yet — that's a future tightening), but here are useful conventions:

- `status_change` — "saved -> applied"
- `message_sent` — outgoing DM, LinkedIn, WhatsApp
- `message_received` — incoming reply
- `email_sent`, `email_received` — same but for email
- `application_sent` — clicked apply on a job board
- `interview_scheduled`, `interview_done` — interview lifecycle
- `note` — anything that doesn't fit, free text

Keep `event_type` short, snake_case, predictable. We'll filter and group by it later.

## A worked example — querying the timeline

```sql
SELECT occurred_at, event_type, body
FROM events
WHERE job_id = 1
ORDER BY occurred_at;
```

Returns the full Presolv360 timeline in chronological order. Useful for the "open this job to see history" feature (Ship 6 web UI).

To find jobs you haven't touched in 5+ days:

```sql
SELECT id, title, status, last_activity_at
FROM jobs
WHERE worth_pursuing = 'yes'
  AND date(last_activity_at) < date('now', '-5 days')
ORDER BY last_activity_at;
```

That's the "going cold" detector we sketched in the requirements.

## Check yourself

- Why do we keep BOTH a `status` field AND an `events` table, instead of just one?
- What's the difference between `occurred_at` and `recorded_at`?
- If you wanted to find "all jobs where I haven't heard back in >5 days," what would the query look like?
- Why is `event_type` a free string instead of a strict enum (today)?

## Interview-ready 60-second answer

*"State machines and event logs are standard patterns. A status field gives fast current-state lookups; an event log gives an immutable history for audit, debugging, replay, and analytics. Pure event sourcing — deriving state by replaying events — works for some domains (finance, audit) but is usually overkill; most apps maintain both, computing status at write-time. Two timestamps per event — `occurred_at` (when it happened) and `recorded_at` (when it was logged) — handle backfilling cleanly. State transitions can be validated against an allowed-moves table; in early stages you typically allow any string and tighten later."*

## Open threads

- **Strict transition validation** — table of allowed (from, to) pairs; defer
- **Event-derived analytics** — average time-to-reply, reply rate per channel; comes later when we have data
- **Soft delete via events** — mark something `archived` instead of deleting; events make it reversible
- **Webhooks / triggers** — events that fire automated actions (e.g., "if no activity for 7 days, auto-flag stale"); much later
- **Pure event sourcing** — no status column, status is computed every read; not needed at our scale
- **UTC vs local time** — production usually stores UTC; we're using local ISO 8601 for simplicity
