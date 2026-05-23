# Design Prompt for Claude (for use at claude.ai / Artifacts)

Paste the **entire block below** into a fresh Claude.ai conversation. Ask Claude to produce:
1. A design system (color tokens, typography, spacing, component primitives)
2. Six key screen designs (HTML+Tailwind artifacts so you can preview live)
3. A component library (cards, badges, buttons, modals, comments)

After the first pass, iterate with follow-ups: *"now show me the Add Job modal in dark mode,"* *"redesign the activity timeline,"* etc.

---

## ===== PROMPT START — paste this into Claude.ai =====

You're designing the UI for a **personal job-application tracking webapp**. I'll give you the full context, user persona, current pain points, required screens, and visual direction. Produce a complete design system + the six key screens listed at the bottom. Output HTML+Tailwind via CDN as Artifacts so I can preview live.

### Product context

**Job Tracker** is a personal command-center webapp for active job seekers. It manages the application lifecycle end-to-end: from "I saw a LinkedIn post" → "I got an offer," with AI brains analyzing each lead's JD, company, hiring team, then drafting tailored resumes and outreach messages.

The data model already exists (FastAPI + SQLite). The current UI is functional but ugly — vertical lists, no pipeline visualization, no comments, no filters. We need a redesign.

### User persona — be specific

- **Name:** Ajinkya Kate. **Role:** Product Owner at a B2B SaaS company (recently displaced). **Experience:** 2+ years PM, CSPO certified. **Location:** Pune, India.
- **Volume:** 10–20 applications/day across LinkedIn, Naukri, direct outreach. Active pipeline of 15–25 leads at any time.
- **Yield reality:** ~10–15% reply rate. Most jobs go silent. Emotionally tired but ambitious.
- **Tech aesthetic:** Tech-savvy Gen-Z. Power user. Wants speed, dense information, minimum clicks. Comfortable with Linear / Notion / Vercel-style modern interfaces.
- **Devices:** Primarily Mac (desktop, 13"–15" screens). Secondary: phone (iPhone, mobile Safari). Same data accessible on both.

### What the user does on the app, in priority order

1. **Triage new leads** — paste a LinkedIn URL or screenshot, instantly see structured analysis + suggested actions
2. **See "what to do today"** — surface the 3–5 jobs that need action right now (call due, follow up due, draft to send, application waiting)
3. **Move jobs across stages** — drag from Saved → Applied → Replied → Interview → Offer/Reject. Or send to Backlog.
4. **Download tailored resume per job** — click → PDF saves with company name in filename
5. **Copy drafted messages** — connection notes, follow-ups, cold DMs, with one-click copy
6. **Add comments / notes** — chat-style timeline of thoughts ("Aditi replied positively," "follow up Tuesday," etc.)
7. **Filter / search** — by status, company, fit-score, has-warm-contact, recently-active

### Multi-brain output (this is the killer feature, design for it)

When user pastes a JD or job link, the app runs five "AI brains" and shows their outputs together on the job card:

1. **JD Analysis Brain** — extracts: title, level, YoE required, must-have skills, nice-to-haves, comp signal, urgency cues (recent post? actively reviewing?)
2. **Company Profile Brain** — what they do, employee count, recent signals (hiring spree? layoffs? funding?), product summary
3. **Persona Analysis Brain** — for each visible hiring-team contact: role, seniority, mutual connections, DM tone recommendation (warm/formal)
4. **Resume Brain** — proposes 3–5 bullet-level tweaks to the user's master resume tailored to this JD (highlights keyword matches, surface buried wins)
5. **Outreach Brain** — drafts: (a) LinkedIn connection-request note (200 char), (b) follow-up DM after accept, (c) cold-DM to decision-maker as fallback

Show these as expandable cards or tabs within the job's expanded view. Each card has Copy / Apply / Discard actions.

### Current UI pain points to fix

1. **No pipeline visualization** — current dashboard is a vertical list sorted by `worth_pursuing`. We want a **horizontal Kanban** with columns per status.
2. **No drag-to-change-status** — currently user runs CLI commands. Needs to be drag-and-drop in the web UI.
3. **No inline comments** — user wants to add timestamped thoughts to each job ("called Latika, voicemail"). Currently events are append-only via CLI.
4. **No filtering** — can't say "show only saved-pursue=yes jobs in B2B SaaS." Needs a filter bar.
5. **Activity timeline is buried** — bottom of the detail page. Should be a sidebar or right-rail widget.
6. **AI brain outputs are mixed in with regular events** — currently all in one activity log. Should be grouped + prominent.
7. **No quick-add** — currently means opening terminal and running a CLI command. Need a floating "+ Add Job" button + modal.
8. **No filename context when downloading resume** — fixed but want to surface "tailored for this job" status clearly.
9. **No "fit score" visualization** — each job has an implied fit (from JD vs user profile). Should be visual (badge, ring, color).
10. **No notion of "warm-in path" visualization** — when a job has a strong warm-in contact (mutual connections, alumni, etc.), it should be visually distinct on the card.

### Six required screen designs

Produce each as a standalone artifact (HTML+Tailwind CDN, rendered in dark mode + light mode toggle):

#### Screen 1: Dashboard — Pipeline Kanban (PRIMARY VIEW)
- Horizontal scrolling columns by status: **Saved | Applied | Replied | Interview | Offer | Rejected | Backlog**
- Each column header shows count + collapse/expand
- Each card in a column shows: company logo placeholder, job title (1 line truncated), company name, fit-score badge (color-coded), next action date (red if overdue), 1-line activity, warm-contact indicator if any
- Drag-to-reorder within column, drag-across columns to change status
- Top: title "Job Tracker", today's date, top stats (5 cards: due today, upcoming, active total, response rate, offers)
- Right side: filter chips (status, fit, has-warm-contact, last 7 days) + global search
- Floating action button bottom-right: "+ Add Job" (opens Add Job modal)
- Empty column states ("No jobs in this stage yet")

#### Screen 2: Job Card (Expanded — Multi-Brain View)
- Modal or full-page detail view triggered by clicking a card
- Header: company logo + title + company + status badge + fit-score + action buttons (Mark Applied, Mark Replied, etc.)
- Below header: 5 horizontal tab cards (or stacked sections) for the 5 AI brain outputs
  - **JD Brain** — extracted requirements as chip groups + raw JD collapsible
  - **Company Brain** — bullet summary + key facts
  - **Persona Brain** — list of hiring-team contacts with their LinkedIn previews + DM tone recommendation
  - **Resume Brain** — current master resume → proposed tweaks (diff style) → "Download Tailored PDF" button
  - **Outreach Brain** — 3 message drafts as cards with Copy buttons + Send Tracking
- Right rail: Activity Timeline (events + comments, reverse-chronological with timestamps)
- Bottom: Comments composer (chat-style, supports markdown, "Add comment" → updates timeline)
- Quick actions bar: Apply via Link, Open LinkedIn (contacts), Schedule Follow-up, Move to Backlog

#### Screen 3: Add Job Modal
- Floating modal triggered by FAB
- Three tabs: **Paste URL** | **Paste JD Text** | **Manual Entry**
- Paste URL: single input, "Analyze" button → loading state → preview of extracted fields → "Add to Pipeline"
- Paste JD: large textarea, optional company name + role title, "Analyze" → preview → Add
- Manual Entry: form fields
- After "Analyze": show extracted preview with confidence indicators per field, user can edit before saving
- Saves directly into "Saved" column on pipeline

#### Screen 4: Today View / Daily Briefing
- Mobile-first design (phone primary use)
- Top section: "Good morning, Ajinkya — here's your queue for today"
- 3–5 action cards stacked, each = one job that needs action today
- Each action card has: company + role + specific action ("Call Latika at +91-..." or "Send DM to Athar with this draft") + Copy buttons inline
- "Mark Done" swipe gesture on mobile
- Bottom: "Catch up section" — leads going cold (no activity 5+ days), oldest first

#### Screen 5: Resume Studio
- Side-by-side: left = master resume (markdown source), right = tailored output for current job
- Top: dropdown to switch which job's tailoring you're viewing
- Inline diff highlights: green = added bullets, blue = modified bullets, gray = unchanged
- Right-side "AI suggestions" panel: 3–5 specific tweaks with one-click Apply
- Bottom: "Save & Generate PDF" + "Apply with this resume" buttons
- Preview mode toggle: see rendered HTML version (matches the PDF)

#### Screen 6: Settings / Profile
- Master resume editor (markdown)
- User profile (name, contact, LinkedIn, GitHub)
- Anthropic API key field (password input, "Saved" indicator)
- Theme toggle (light / dark / system)
- Data export (download tracker.db, export all jobs as CSV/JSON)
- About (version, GitHub link)

### Design system requirements

Define and use consistently across all screens:

**Color tokens (light + dark mode):**
- Background levels (base, raised, sunken)
- Text (primary, secondary, tertiary)
- Accent color (one strong primary — purple? blue? user pick)
- Status colors: saved=gray, applied=blue, replied=amber, interview=green, offer=emerald, rejected=red, backlog=zinc
- Semantic: success/warning/error/info

**Typography:**
- Inter font (with system fallback)
- Type scale (display, h1, h2, h3, body, small, caption)
- Tabular numbers for stats

**Spacing:** 4px base unit. Common: 4, 8, 12, 16, 24, 32, 48, 64.

**Components to define and reuse:**
- Card (default, hover, active, disabled states)
- Button (primary, secondary, ghost, destructive, icon-only)
- Badge / chip (status, fit-score, count)
- Avatar with initials fallback
- Modal (lightweight, focuses content)
- Tab strip (segmented, underline-style)
- Input + Textarea + Select
- Comment thread item (timestamp, author, body, reactions)
- Toast / notification
- Activity timeline item
- Empty state
- Loading skeleton

**Interaction patterns:**
- Drag-to-move (kanban cards across columns)
- Inline expand / collapse (cards, sections)
- Keyboard shortcuts: `n` = new job, `/` = focus search, `e` = expand selected card
- Click + cmd-click multi-select
- Optimistic UI for status changes (update instantly, sync server)
- Toast confirmation on successful actions
- Modal close: backdrop click, ESC, close button

**Visual style direction:**
- Modern, tech-aesthetic (Linear / Notion / Vercel inspiration)
- Subtle borders, generous whitespace, micro-interactions
- Dark mode by default for desktop; light mode for phone (matches OS)
- Accent color used sparingly (only on primary actions + status moments)
- Status colors as the only "loud" color usage

### Tech constraints

These designs will be implemented in:
- FastAPI server-side rendering (Jinja2 templates)
- Tailwind via CDN (no build step)
- HTMX for interactivity (no React)
- Vanilla JS for small interactions (drag-and-drop, modal management)
- Designs should be achievable without a heavy JS framework

### Output format

For each screen, produce:
1. **Title + description** (what this screen is, when it's used)
2. **Live HTML+Tailwind artifact** (renders standalone in browser)
3. **Annotations** below each design: callouts on interactions, edge cases, mobile behavior
4. **Component inventory** — list which design-system components the screen uses

For the design system itself, produce:
1. **Color palette** as Tailwind config tokens (light + dark)
2. **Component library** as a single HTML artifact showing all components in all states
3. **Spacing + typography reference card**

Start with the **design system** (single artifact). Then **Screen 1: Dashboard Pipeline Kanban** (the most important one). Then iterate from there. After each artifact, pause and ask if direction is right before continuing.

## ===== PROMPT END =====
