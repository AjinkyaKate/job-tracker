# Horizontal Jobs List

_Started 2026-05-23 22:31 UTC_

---

## User

<system-info comment="Only acknowledge these if relevant">
Project title is now "JD"
Project is currently empty (no files)
Current date is now May 24, 2026
</system-info>

<default aesthetic>
If no references, art direction or design systems were provided, use this default professional modern, minimal aesthetic as a base. Declare your choice out loud so you stick to it. Guidance:
- Choose a type pairing from web-safe set or Google Fonts. Helvetica is a good choice. Avoid hard-to-read or overly stylized fonts. Use 1-3 fonts only.
- Foreground and background: choose a color tone (warm, cool, neutral, something in-between). Use subtly-toned whites and blacks; avoid saturations above 0.02 for whites.
- Accents: choose 0-2 additional accent colors using oklch. All accents should share same chroma and lightness; vary hue.
- NEVER write out an SVG yourself that's more complicated than a square, circle, diamond, etc.
- For imagery, never hand-draw SVGs; use subtly-striped SVG placeholders instead with monospace explainers for what should be dropped there (e.g. “product shot”)

CRITICAL: ignore default aesthetic entirely if given other aesthetic instructions like reference images, design systems or guidance, or if there are files in the project already.
</default aesthetic>

<pasted_text name="Pasted text (183 lines)">
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

</pasted_text>

<!-- The user explicitly selected the following skills for this project, as attachments to their message. These are not optional context — they define how you work. Use them. -->
<attached-skill name="Hi-fi design">
Create a high-fidelity, polished design. Follow the instructions about design in your system prompt, particularly the 'How to do design work' section. Use the design_canvas starter component, or make a full-bleed prototype and offer options via Tweaks.
</attached-skill>

<attached-skill name="Interactive prototype">
Create a fully interactive prototype with realistic state management and transitions. Use React useState/useEffect for dynamic behavior. Include hover states, click interactions, form validation, animated transitions, and multi-step navigation flows. It should feel like a real working app, not a static mockup.
</attached-skill>


<system-reminder>Auto-injected reminder (ignore if not relevant): do not recreate copyrighted or branded UI unless the user's email domain matches that company. Create original designs instead.</system-reminder>

## Assistant

_[tool: update_todos]_

I'll build this in the order you asked: design system first (single artifact), then Screen 1 (Dashboard Pipeline Kanban), then pause for your direction before the rest.

A few decisions I'm locking in up front so the system is consistent:

- **Font:** Inter for UI, JetBrains Mono for metadata/numbers (tabular)
- **Accent:** electric violet `oklch(0.62 0.19 290)` — sparing usage, primary actions only
- **Status palette:** desaturated in dark mode, slightly more saturated in light, as Linear/Vercel-style modern UIs do
- **Theme:** dark default with a toggle, both rendered in the same artifact
- **Stack:** plain HTML + Tailwind CDN + a tiny bit of vanilla JS (no React) so it maps directly to your Jinja+HTMX implementation

_[tool: write_file]_

_[tool: write_file]_

Now Screen 1 — the kanban. I'll wire it up with real drag-and-drop, working filter chips, search, an Add-Job FAB that opens a real modal, and clickable card → detail drawer preview. All vanilla JS so it maps to your HTMX stack.

_[tool: update_todos]_

_[tool: done]_

Pausing here for your direction check — as requested. Two files are ready for review:

- **`design-system.html`** — color tokens (dark + light), type scale, spacing, full component library: buttons in all states, status/filter chips, fit-score rings, warm-in indicators, form controls, tab strips, job-card states (default/hover/selected/dragging/overdue/empty drop slot), brain output cards, comment thread, activity timeline, modal preview, toast, empty state, skeletons, keyboard map.

- **`01-dashboard-kanban.html`** — the primary view, fully interactive:
  - 7 columns (Saved → Backlog) with realistic Pune/B2B-SaaS data, ~22 jobs
  - **Drag & drop works** — move cards within or across columns, with a violet placeholder line showing drop position, drop-zone tinting, and a toast confirmation
  - **Filter chips** (Fit ≥ 70 · Warm contact · B2B SaaS · Active 7d · Overdue) — toggle them, counts update like `12/22`
  - **Search** (press `/` to focus) filters across all cards
  - **`N`** opens the Add-Job modal (real backdrop, ESC closes)
  - Stats strip shows due-today, upcoming, total, reply rate, offers
  - Each card carries: status-tinted initials block, role, company + city, fit-score ring (color ramps by tier), 1-line activity, next-action with overdue red treatment, warm-mutuals chip, HOT badge, event count

A few choices I want to flag so you can redirect before I build the rest:

1. **Accent = electric violet.** Used sparingly — primary CTA, selection ring, warm-in chip, drop placeholder, brand mark only. Want to try a different hue (blue / emerald / orange)?
2. **Status colors are low-saturation** in dark mode (Linear-style) and travel as tints, not heavy fills. Switching to bolder blocks is a one-token change.
3. **Card density** — currently ~112px tall with role, company, fit ring, activity line, next-action, warm chip, event count. Could go denser (drop activity line) or roomier (add a second line). Where do you want to land?
4. **Pipeline columns shown 1:1** matching your spec (Saved · Applied · Replied · Interview · Offer · Rejected · Backlog). Some users prefer Rejected + Backlog hidden under a "Closed" toggle. Worth it?
5. **Brain outputs** — I'm leaning **stacked sections** (not horizontal tabs) on the job-detail screen so the user can scan all 5 brains at a glance. Confirm or push back?
6. **Stat cards** — I went with 5 small tiles. They can be more chart-y (sparklines on each) or collapse into a single condensed strip. Preference?

Tell me what to change and I'll continue with **Screen 2 (Job Detail · multi-brain)** next.

## User

can you give one option like horiznonatl list view of this jobs

## Assistant

_[tool: str_replace_edit]_

Adding a List view toggle right next to the filter bar. Same data, table-style rows — denser, sortable, better for triaging 20+ jobs in one sweep.

_[tool: done]_

Added a **Board / List** toggle on the right side of the filter bar.

**List view** is the same data laid out as a table:
- Rows grouped by status, with a sticky group header (status dot + label + count) for each section
- Columns: initials block · Role + Company · Status pill · Fit (mini ring + number) · Next action · Latest activity · Warm-in chip · Event count
- Sortable column headers (Role A→Z and Next action ascending are pre-indicated)
- Clicking a row triggers the same detail-open flow as the card
- Filters and `/` search work identically — group counts switch to `n/total` when filtered, and empty groups auto-hide

Try toggling **Board ↔ List** in the top-right of the filter bar.

_[tool: fork_verifier_agent]_

Toggle is live — try it and tell me whether to lock that in, push for a denser/wider list, or move on to **Screen 2 (Job Detail · multi-brain)**.

## User

Verifier agent check completed

## Assistant

Verifier confirms both views render cleanly. Ready for your call on direction — lock this in and proceed to **Screen 2 (Job Detail · multi-brain)**, or refine the kanban/list further first?

## User

okay

## Assistant

_[tool: update_todos]_

Moving to **Screen 2 — Job Detail (Multi-Brain View)**. Using Razorpay · Senior PM as the focal job (the same record from the kanban) so the data is continuous.

_[tool: write_file]_

_[tool: done]_

_[tool: update_todos]_

**Screen 2 · `02-job-detail.html`** is live.

Layout:
- **Top bar** with breadcrumb (Pipeline / Applied / Razorpay · Senior PM) and `J/K` prev-next hint
- **Job header** — RP logo, full role title, status pill, location, comp, JD link, urgency strip (posted 3d ago · 1.2k applicants · actively reviewing · 2 warm contacts), big fit ring (78), Mark Replied + Schedule actions
- **Sticky sub-nav** — JD · Company · Persona (3) · Resume (5 tweaks) · Outreach (3) with anchor scroll + auto-highlight on scroll. Quick actions on the right (Apply via link · Follow-up · Move to Backlog)
- **5 stacked brain cards** (your data model exactly):
  1. **JD Brain** — level/YoE/domain/reports-to, must-have skills with `·match` / `·gap` chips, nice-to-haves, raw JD collapsible, side "Signals" rail with verdict
  2. **Company Brain** — narrative summary, 4 numeric tiles (employees, funding, PM org size, Glassdoor), recent signals, key-facts rail
  3. **Persona Brain** — 3 contact cards (HM, recruiter, skip-level VP), each with mutuals avatars, DM tone recommendation, response-rate signal, per-contact action buttons including avoid-cold-DM warning for the VP
  4. **Resume Brain** — 5 proposed tweaks rendered as **diff lines** (green=add, blue=rewrite, red=del-strike, gray=context). Each tweak has its own Discard/Apply. Download button reads `Razorpay_AjinkyaKate.pdf`
  5. **Outreach Brain** — 3 message drafts as side-by-side cards (Connect 200-char / Follow-up after accept / Cold to recruiter), each with char count, tone chip, Regenerate + Copy, footer to mark each as sent
- **Brain-status strip** above the stack: per-brain confidence pill + "Re-run all" + "last run 11 min ago"
- **Right rail (360px)** — Activity timeline grouped by day (Today / Yesterday / Earlier this week), filter toggle All · Brains · Notes, comments inlined among events with their own card style, composer pinned to bottom with markdown affordances + ⌘↵

Tell me if anything's off — happy to:
- Switch the 5 brains from stacked to horizontal tabs
- Trim the activity rail (it's verbose by design — power-user pref)
- Adjust the persona card density
- Move on to **Screen 3 — Add Job modal** (which exists as a preview in Screen 1; I'll build the full version next with the three input modes + extraction preview + confidence-per-field UI)

## User

Screen 3

