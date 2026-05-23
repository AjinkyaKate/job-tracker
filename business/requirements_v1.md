# Job Tracker — Requirements v1

> Live document. Grows session by session. Last updated: 2026-05-23.
> Process: every question asked and answered is logged in §8 "Conversation log" so the folder explains itself.

## Status

| Step | Status |
|---|---|
| 1. Discover the user | ✅ Done — corrected for real persona in S4–S5 |
| 2. Find the pain | ✅ Done — full pain table populated S5 |
| 3. Current workarounds | ✅ Done — none (memory only) |
| 4. Define success | ✅ Done — north-star = offers; leading = response-rate baseline 10–15% |
| 5. Pin down scope | ✅ Done — Phase 1 anchored on (b) "Never Lose a Thread" |
| 6. Validate | ✅ Done — user picked anchor in S6, scope frozen |
| 7. Document | ✅ This file; Phase 1 Charter in §9 |

## 1. User profile

- **Name:** Ajinkya Kate (also the project owner)
- **Role / experience:** Product Owner at D·engage; 2+ yrs PM experience; CSPO certified — mid-level, not senior
- **Current situation:** recently lost role; in active job search in the Indian PM market
- **Volume signal:** 10–20 applications/day (S3 Q1) — high effort
- **Yield signal:** *"a lot of time I spent but there is no output"* (S3 Q5) — low conversion
- **Response rate (S5 Q3):** ~1–3 replies per 20 apps → **~10–15%**, mostly silence
- **Today's behavior pattern (S5 Q1):** LinkedIn easy-apply with **one resume** to every job, almost no outreach; warm-connection messaging when triggered, no cold outreach
- **Emotional state (S5 Q4):** *"very tired, stuck, ambitious, hopeless, very frustrating"* — design for this honestly, don't paper over it
- **Channels:** LinkedIn discovery, Naukri, occasional founder/HR outreach
- **Tech comfort:** strong product instincts, moderate technical depth (learning to build via this project)
- **Dual role:** he is both the user and the FDE-in-training on this project

### Persona calibration (corrected after S4 user feedback)

The user is **NOT** a high-functioning senior PM with recruiters lining up.

He is a mid-level Product Owner in a tough job market, recently displaced, anxious, time-pressured. His pattern is **high effort, low yield** — 10–20 applications/day, very few replies. Many threads juggled in his head, no system, no reliable workaround.

**Implications for product decisions:**
- A "manage your pipeline like a pro" UX is *wrong* if the reality is "I sent 15 messages and heard back from 1."
- The tool's job is to make a **leaky funnel survivable**, not optimize a healthy one.
- Emotional reality matters: tired, anxious, possibly numb. The UX should reduce overhead, not add it.
- Quick wins matter more than completeness. A "you got 1 reply this week — here it is, here's a draft response" is more valuable than a comprehensive funnel chart.

### Language calibration for FDE work (S4)

When asking discovery / validation questions: **use plain, concrete, story-based language.** Avoid PM/UX abstractions ("where does it feel wrong", "what's missing", "what's overkill"). Those make the user imagine a product instead of describing their day. Ask about today, about a specific job, about real moments — not about a hypothetical tool.

## 2. Pain (synthesized from Sessions 1–2)

### Confirmed pains, with evidence

| Pain | Evidence (Session) | Type of cost |
|---|---|---|
| **No tracking system at all — pure memory** | S2 Q1 verbatim | Everything else cascades from this |
| **Wrong resume surfaces in interview** | S2 Q2 — interviewer asks questions from a resume Ajinkya doesn't remember sending | **Reputational** (loses credibility mid-conversation) |
| **Follow-up paralysis** | S2 Q2 — "I am not able to follow up with the respective person" | Opportunity loss; leads go cold |
| **Multi-touchpoint threads kept entirely in head** | S2 Q3 (Mumbai story: founder → HR → ?) | Drops between handoffs; can't resume after a gap |
| **No conversation context when replying** | S2 unprompted — wants to see last message before crafting next | Bad replies; misses cues |
| **Re-reading every JD to figure out level/YoE/skills** | S1 | Reading fatigue; slows top-of-funnel |
| **No funnel view** | S1 | Can't tell where time is being lost |
| **Time invested ≠ output produced** | S3 Q5 verbatim — "A lot of time I spent but there is no output" | **The core pain.** All other pains roll up to this. |
| **Same resume to every LinkedIn job** | S5 Q1 — no tailoring per role | Mediocre fit; wastes any tailoring advantage |
| **Outreach messages don't get replies** | S5 Q1 — warm connections not replying | Effort with no return → learned helplessness |
| **Cold-outreach paralysis** | S5 Q1 — "no cold call" | A whole channel is unused — wants to start but doesn't |
| **No contact-discovery workflow** | S5 Q2 — wants tool to find phone numbers, esp. from HR emails | Manual contact-hunting today |
| **Channel ladder lost** | S5 Q2 — wants to track LinkedIn DM → email → phone progression | One thread per channel, can't see full conversation |
| **Emotional cost: hopelessness** | S5 Q4 verbatim | Affects engagement with the tool itself — UX must not add weight |

### Volume + yield (Sessions 3, 5)

- **10–20 applications per day** (50–140/week)
- **~10–15% response rate** (1–3 replies per 20 apps)
- Most touches end in silence. The product must make a leaky funnel survivable.

## 3. Current workarounds — confirmed: NONE

User confirmed (Session 2 Q1 verbatim): **the only "system" today is memory.**
- LinkedIn + Naukri for discovery
- Email for outreach, sent when remembered
- No spreadsheet, no notes app, no Notion, no CRM, no calendar reminders

**FDE read:** absence of a workaround is itself a signal. Two possibilities:
- (a) pain is real but the user hasn't built a workaround — likely because cognitive load on the job-hunt itself is already high
- (b) pain is bearable enough that no investment has been made

Given the reputational cost of wrong resumes and the multi-touchpoint thread drops, **(a) fits.** The tracker fills a real gap; it doesn't displace anything.

## 4. Success criteria

### North-star metric (user's words, S3 Q4)
**Offers landed / conversion rate.** "How much we convert, how many offer letters we are getting."

This is *lagging* — measurable only after weeks/months. The whole project's success will eventually be judged here.

### Reframe — value is output per hour, not hours saved (S3 Q5)

User explicitly said: *"A lot of time I spent but there is no output. There should be output by giving that many hours per day and we should get some. In the minimum time we get a fast output."*

So the metric the tool should optimize is **output ÷ hours invested**, not "hours saved." The user is willing to put in the time. The tool's job is to turn that time into results.

**Implication:** every feature should be evaluated against: *"does this raise offers per hour of effort?"* A feature that makes tracking prettier but doesn't move the ratio is decoration, not value.

### Leading indicators (instrument these to know early if it's working)

| Metric | Why we need it |
|---|---|
| Reply rate (replies / outreach sent) | First proof outreach is landing |
| Interview rate (interviews / applications) | Funnel health |
| Time-to-first-reply | Speed signal |
| % jobs whose status moves forward each week | System keeping leads alive |
| % leads going cold (>N days stale) | Should trend down — currently this is the leak |
| Reply rate **by resume variant** | Tells user which resume converts; feedback into resume strategy |
| Reply rate **by outreach channel** | LinkedIn DM vs email vs referral — double down on what works |

Dashboard should surface these so the user can see "is the time invested actually producing leads?" without waiting months for offer-letter data.

## 5. Scope (updated after Session 2)

### New in Session 2 (from user's unprompted requirements)

The Mumbai-story incident surfaced two requirements that reshape the data model:

**5a. The status model must support TWO flows, not one.**

- **Flow A — Direct apply** (no human contact, just clicking apply on a job board):
  `Saved → Applied → (Silence | Rejected | Interview-invited)`
- **Flow B — Outreach-driven** (with intermediaries):
  `Saved → Reached-out (intermediary, e.g. founder) → Got-intro → Reached-out (HR/recruiter) → Replied → Applied → Interview → Offer/Reject`

A job can switch flows mid-stream (e.g., started as direct-apply, then got a referral). Status model has to accommodate that.

**5b. Conversation context per contact must be visible.**

Per contact, the system stores the messages exchanged (at minimum: their last message, our last message, channel). When drafting a reply, the user sees the thread context. The AI outreach feature must *use* this context, not just the JD.

**Data-model implication:** the original `events` table is insufficient. We need a `messages` table:
```
messages: id, contact_id (FK), direction (in/out), channel (linkedin/email/phone), body, sent_at
```

### Full MoSCoW (updated)

**Must have**
- Save job by URL or paste
- Auto-extract role / YoE / skills / summary via AI
- Store HR/recruiter contact per job (multi-contact per job — e.g., founder + HR)
- Status tracking supporting **both Flow A and Flow B** (see 5a)
- Conversation log per contact — at minimum, last-message-in/out (see 5b)
- Follow-up reminders
- Multiple resume variants, tagged
- Record of which resume was sent to which job

**Should have**
- AI recommends best resume per JD
- AI drafts outreach messages that incorporate the conversation context (not just the JD)
- Funnel dashboard

**Could have**
- AI suggests resume tailoring per JD
- Email reminder integration
- Automatic message sync (pull LinkedIn DMs / Gmail) — high value, high risk; defer

**Won't have (now)**
- Multi-user / SaaS
- Auto-apply to jobs
- Mobile native app
- Browser extension scraping at scale

### 5d. Phase 1 scope freeze (Session 6) — anchor: "Never lose a thread"

After scope ballooned through Sessions 1–5 to seven distinct capabilities, user picked one anchor in Session 6 to make the first ship achievable. **Phase 1 builds only this; everything else moves to the roadmap.** See §9 for the full charter.

**In Phase 1 (Must):**
- Add a job (manual entry: title, company, link, optional JD text pasted in)
- Add multiple contacts per job (founder, HR, recruiter — each a row)
- Log messages per contact (paste in/out body, channel, date)
- Status per job supporting both flows (direct-apply / outreach-driven; see §5a)
- "What needs action today" view — follow-ups due, recent replies, stale threads
- Record which resume label was sent per job (just a field; resume registry stays light)

**Phase 1 deferred to roadmap:**
- All AI features (JD extraction, message drafting, resume recommendation, contact extraction) → Phase 2+
- Cold-outreach onboarding (R4) → Phase 2+
- Multi-channel ladder *suggestions* (R5) → partial; we track channel per message, but no "what comes next" UI
- Funnel analytics dashboard → Phase 2+
- Web UI → Phase 3+ (CLI only in Phase 1)

### 5c. Volume implications (Session 3)

User does **10–20 applications/day** (50–140/week). This reshapes Must-Have UX:

- **Adding a job must be fast (<30 seconds end-to-end).** No 5-question CLI wizard. Either: one-shot `add <url>` with all defaults, or batch.
- **Batch operations** — paste several URLs at once; system processes them in the background.
- **Funnel view is critical** — by week 2 there will be 100+ open apps. Need filters and sort by "needs action today."
- **AI JD extraction moves from Should-Have to MUST-Have.** Manually reading ~100 JDs/week is impossible. Without AI, the tool fails.
- **Dashboard must surface what's converting** (by resume variant, by channel) so user can double down on winning patterns. Pure tracking is not enough; tracking + insight is the deliverable.
- **Ruthless filtering UI** — at this volume, the user spends more time *deciding what to act on next* than entering data. Default view: "5 things that need action today."

## 6. User stories

Captured in project root `CLAUDE.md` §3 (10 stories). Will be re-validated after pain/success gathering completes.

## 7. Non-functional requirements

- **Privacy:** all data is personal — no third-party telemetry. Resume PDFs stay private.
- **Reliability:** if AI extraction fails, user can always fall back to manual entry. Never a dead end.
- **Speed:** "add a job" should feel fast (≤10 seconds end-to-end including AI call).
- **Cost:** AI usage at personal-scale should be cents/week, not dollars/day.
- **Recovery:** all data is local-first; backups easy.

## 8. Conversation log + open questions

### Session 1 — 2026-05-23 (kickoff)

**What happened:** Ajinkya described the problem in his own words. The FDE captured the initial persona, painted a draft scope, made foundational decisions (CLI-first, both URL + paste, heavy AI, no fixed cadence).

**Decisions logged:** see project `CLAUDE.md` §8.

**Open questions to close in Session 2:**

> **Q1. Volume.** Roughly how many jobs do you apply to per week? Of those, how many involve messaging a recruiter or HR directly (vs. just clicking "Apply")?

> **Q2. Current workaround.** What do you use *today* to track this — a spreadsheet, Notion, a notes app, just memory, or nothing? Walk me through it. Where does it fail?

> **Q3. Last incident.** Tell me about the last time something went wrong — you sent the wrong resume, forgot to follow up, or couldn't remember who you'd messaged. What actually happened?

> **Q4. Success metric.** If this thing works perfectly in 3 months, what *one number* about your job hunt changes that you'd notice? (Reply rate? Interview count? Time spent on admin?)

> **Q5. Time budget.** Roughly how much time per week do you spend right now on the *admin* of job-hunting (tracking, following up, finding the right resume) vs the actual *doing* (writing applications, talking to recruiters)? What's an acceptable amount?

### Session 2 — 2026-05-23 (pain + workaround + first incident)

**Q1 — Volume.** *How many jobs/week? How many involve recruiter messaging?*

Answer (verbatim):
> "Currently I do it manually. I go to LinkedIn, go to the Naukri and apply to the job. If I remember I send the email. There is no tracking system used, nothing, just memory."

What we got: confirmation that the current system is **human memory**. Email follow-ups are sporadic, triggered by recall.
What's still missing: **the actual number** (apps/week, outreach messages/week). Pushed back to user to answer.

---

**Q2 — Current workaround.** *What do you use today? Where does it fail?*

Answer (verbatim):
> "Yes actually there are multiple times when I share a different resume and then the interviewer asks me a different question on that resume. That also happens. I am not able to follow up with the respective person as well."

What we got: two concrete failure modes:
- **Wrong resume in interview** — interviewer references content from a resume Ajinkya doesn't remember sending; caught off-guard mid-conversation. **Reputational cost**, not just admin annoyance.
- **Cannot follow up** — even when willing, doesn't know who/when/what to say.

---

**Q3 — Last incident.** *Walk me through the last time something went wrong.*

Answer (verbatim):
> "Today what I do is I search for a job. I got to know about a city product manager role at some company based in Mumbai so I reached out to their founder and he accepted my request. I messaged him and shared the HR details. The HR replied and I will go to the profile and let me know."

What we got: a real-world **multi-touchpoint outreach flow**:
1. Discovered job (city PM role, Mumbai-based company)
2. Reached out to **founder** on LinkedIn → connection accepted
3. Founder shared **HR contact**
4. HR replied — but next step ambiguous, status unclear
5. **All of this is in Ajinkya's head.** No record anywhere.

---

**Unprompted requirements user volunteered** (capture, don't lose):

- "We want to track everything properly" — granular status tracking
- "What if we do not message, we just apply? What then?" — two distinct flows: direct-apply vs. outreach-driven (captured in §5a)
- "If we go to that particular chat we can find the people and reach out. What is their last message" — conversation context surfacing (captured in §5b)
- "Based on that we can edit our response to the message" — AI drafts incorporate conversation context, not only JD

---

**Still open after Session 2:**
- Q1 (volume — number still missing)
- Q4 (success metric — what number changes in 3 months?)
- Q5 (time budget — hours/week spent on admin today; acceptable target?)

### Session 3 — 2026-05-23 (volume + success + time)

**Q1 (re-asked) — Volume.**

Answer (verbatim):
> "I roughly like ten, ten, fifteen, twenty jobs daily."

What we got: **10–20 applications per day** (50–140/week). High-volume territory. Reshapes UX requirements — see §5c. Confirms AI JD extraction is MUST-have, not nice-to-have.

---

**Q4 — Success metric.**

Answer (verbatim):
> "Success metric is how much we convert, how many offer letters we are getting. That is our success metric."

What we got: north-star is **offers / conversion rate**. Lagging indicator. Tool must also instrument **leading proxies** (reply rate, interview rate, time-to-reply) so we can tell early whether it's working — captured in §4.

---

**Q5 — Time budget.**

Answer (verbatim):
> "A lot of time I spent but there is no output. There should be output by giving that many hours per day and we should get some. In the minimum time we get a fast output."

What we got: **the core pain** of the whole project, surfaced.

User reframed the question. Not "save me X hours" — but "make my hours produce results." Acceptable time spend = whatever it takes, *if there's output*. Unacceptable = current state (lots of time, no output).

The metric the tool optimizes is **output ÷ hours invested**, not hours saved. This reframes every feature decision. Captured in §4.

---

### Session 3 — Validation walk-through (sent to user)

FDE played back the Mumbai scenario tool-mediated to surface gaps. Questions sent to user:
- Where does it feel wrong (not how you'd want to work)?
- What's missing (steps you'd do that the tool isn't capturing)?
- What feels like overkill (friction that wouldn't survive at 15 apps/day)?

Answers will go into Session 4 below, then we close Step 6 and exit business mode for Ship 0 in tech mode.

### Session 4 — 2026-05-23 (user feedback + persona reset)

User pushed back on Session 3's validation questions:

> "the three questions you have asked for the validation are not able to understand like me properly. Think of it as a user like this: this is a specific user. This is not any senior PMs or anything who are getting jobs and calls daily. This is a different user and we want to solve it for this user."

Two FDE mistakes caught:

1. **Questions were too abstract** ("where does it feel wrong / what's missing / what's overkill"). Those force the user to imagine a product that doesn't exist yet. Replaced with plain, concrete, story-based questions about his actual day.
2. **Persona drift** — I'd been writing for a higher-functioning user than the reality. The real user is struggling, not thriving. §1 corrected.

Re-asked, plain-English:
- Walk me through today — what did you actually do for the job hunt, step by step?
- Pick one specific job from the last 7 days. What happened — replied, silent, anything?
- Out of every 10 jobs you apply to, how many reply with a real human response?
- When you sit down to do job-hunt work, what does it feel like?

Validation walk-through deferred until persona is properly grounded by these answers.

### Session 5 — 2026-05-23 (corrected discovery)

User answered all four plain questions. Rich new information; persona substantially clarified; scope expanded considerably.

---

**Q1 — Walk through today (verbatim):**
> "Today what I do is I open LinkedIn and just update my resume and with that same resume I started applying on LinkedIn to every shop. There is no cold call. If there is a connection I try to reach out to that connection but I am still not able to get a reply."

What we got:
- One resume, LinkedIn easy-apply, blanket coverage
- **No cold outreach today** — only warm-connection messaging
- Even warm-connection messages don't get replies
- **Open clarification:** earlier sessions mentioned "different resumes" causing interview mismatches. Today: "same resume." Need to know — are there multiple variants on his machine today, or was that aspirational/past behavior?

---

**Q2 — Pick one specific job (user didn't pick a job; surfaced a capability list instead — verbatim):**
> "We also want to work on that as well: how we can write those messages to the persons so it will benefit that respective person and they will reply to us. How we can email so our communication skill also should be there. How we can get the contacts, like phone numbers of the people, and how we can do cold outreach as well. Also try to find the number as well by going through and seeing. Sometimes there is also a number mentioned by the HR. Try to use that number as well. For example I got the email from the HR. In that email I got the number so the next outreach after the email should be that I will reach out through email only and start the conversation."

**New requirements (R-series):**

| ID | Requirement | Today's gap |
|---|---|---|
| R1 | AI helps write outreach messages the recipient *wants* to reply to (recipient-benefit framing) | Messages today go unanswered — quality, not frequency |
| R2 | AI helps write email — communication-skill coaching, not just generation | User wants to *learn* the craft, not just outsource |
| R3 | Tool surfaces / extracts contact info — phone numbers, emails — from HR replies, JDs, profiles | No structured contact discovery today |
| R4 | Cold-outreach support — onboarding a behavior he doesn't do today | Behavior gap, not just tool gap |
| R5 | Multi-channel ladder tracking — LinkedIn DM → email → phone — system knows what touchpoint comes next | Only one channel tracked per thread today |

---

**Q3 — Reply rate (verbatim):**
> "Out of 10, 20, 20, 20 equals only one, two, three are deploying currently."

Interpretation: **1–3 replies per 20 apps → ~10–15% response rate.** This is the baseline. The tool's first job: move this number up. Captured in §4 leading indicators as the metric we hammer.

---

**Q4 — How it feels (verbatim):**
> "I am very tired, stuck in a normal, so ambitious, also hopeless, also very very. The situation is very frustrating."

**Emotional design implications:**
- Lead the dashboard with action ("3 people to follow up with today"), not metrics ("0 interviews this week")
- Small wins are huge. "1 person replied — here's a draft response" > comprehensive analytics
- Never add overhead; the user is already on empty
- Don't fetishize completeness — "marked all 18 jobs as applied today" is fake productivity

---

**Scope honesty (FDE flag):**

The user has now named at least seven distinct capabilities: tracking, multi-resume, JD extraction, message coaching, contact discovery, cold-outreach onboarding, channel-ladder tracking — plus the original dashboard and follow-up engine. Total scope is now far beyond what a 1–2 month learning project (with a user just starting Python) can deliver.

**Next move:** force prioritization. FDE asked user to pick ONE Phase 1 anchor from four concrete options derived from his answers:
- (a) Better outreach messages (response rate as metric)
- (b) Never lose a thread (Mumbai-flow tracking)
- (c) Cut JD-reading to zero (AI extraction at top of funnel)
- (d) Start cold outreach (contact-finding + first-message drafting)

The others stay in the roadmap; the first ship anchors on the chosen one.

### Session 6 — 2026-05-23 (scope freeze)

**Multi-resume clarification (verbatim):**
> "actually I tried to create multiple resumes but for me managing that with job applications is quite difficult for me right now"

What we got: multi-resume is **real but abandoned**. He tried, the management overhead broke him, he reverted to one. This is meaningful — the resume-management problem is *part of* the tracking problem, not separate from it. When Phase 1 (b) is built, tracking "which resume went to which job" naturally solves a slice of this pain.

---

**Phase 1 anchor pick (verbatim):**
> "I think we can start with the B so we will get some working module of something."

**Decision: Phase 1 = Option (b) — "Never lose a thread."**

The other options stay in the roadmap (see §9 Phase 1 Charter and project `CLAUDE.md` §4 ship plan).

Why this is the right anchor for *this* user:
- Foundational — every other capability (AI message drafting, JD extraction, contact discovery, cold outreach) needs *somewhere to live* in the data model. Build the tracker first; layer everything else on top.
- High emotional payoff — "3 people to follow up with today" gives him action in a hopeless funnel. Concrete moves beat metrics.
- Achievable in 2 weeks while learning Python — the scope is bounded.
- Partially solves multi-resume pain — by tracking "which resume went to which job."

Business mode exits after this session. Tech mode opens next turn (Ship 0).

## 9. Phase 1 Charter — "Never Lose a Thread"

> Final scope freeze for the first ship. Anchored Session 6.

**Premise:** build the tracker that makes a leaky funnel survivable. AI is deferred to Phase 2.

**What "done" looks like:** Ajinkya uses this for one week on real jobs and stops losing threads. Mumbai-style multi-touchpoint flows (founder → HR → ???) survive the week without anything dropping. He can answer "what should I do for the job hunt today?" by opening the tool.

### Must — build in Phase 1
- Add a job: title, company, link, optional pasted JD text, source channel
- Add multiple contacts per job (e.g., founder + HR), each with name, role, email, LinkedIn URL, phone
- Log messages per contact: direction (in/out), channel (LinkedIn / email / phone), body text, date
- Status per job: supports Flow A (direct apply) and Flow B (outreach-driven) — see §5a
- Record which resume label was sent per job (one field, free text or short list)
- "Today" view: jobs/contacts that need action — follow-ups due, replies waiting on response, stale threads (no activity > N days)

### Should — only if cheap inside Phase 1
- Resume registry — a `resumes` table with `label` and free-text `notes`, no AI yet
- Simple stats line at top of "today" view: open jobs, awaiting reply, replies received this week

### Won't — explicitly deferred to roadmap
- AI of any kind (JD extraction, message drafting, resume recommendation, contact extraction)
- Cold-outreach onboarding features
- Channel-ladder "what comes next" suggestions
- Funnel analytics dashboard
- Web UI (CLI only in Phase 1)

### Non-functional
- **Reliability:** never a dead end. Manual fallback for every action.
- **Speed:** add-a-job in <30 seconds end-to-end.
- **Privacy:** all data local; nothing leaves the machine in Phase 1.
- **Recoverability:** all data is in one SQLite file; copying it = backup.

### Acceptance criteria
- [ ] Phase 1 is used by Ajinkya for ≥10 real job applications across at least one week
- [ ] At least one multi-touchpoint thread (with 2+ contacts) is tracked end-to-end
- [ ] At least one follow-up is triggered by the tool's "today" view rather than memory
- [ ] Ajinkya can describe Phase 1 to someone else in <2 minutes (proof he owns the scope, not just the code)

### Exit
On completion, return to business mode for Phase 2 scoping. Likely Phase 2 anchor: (a) better outreach messages, since that's where the response-rate metric moves.

### Session 7 — 2026-05-24 (user journey + 3 new Phase 2 asks)

User articulated his actual job-hunt workflow and dropped three new feature asks. Captured here; integrated into project `CLAUDE.md` §4 ship plan.

**The user journey (verbatim summary):**

1. Open LinkedIn (app or web)
2. Search, filter, scroll; for each job, check JD + experience requirements
3. Click apply link
4. If hiring team is visible, send a message with a note
5. If can't message directly, send a connection request first (with a note)
6. If can message, also try to find their email and reach out there too
7. Apply → update status on phone → follow up later

This journey is **mostly already serviced** by Ships 0–4 (jobs + contacts + status + events + actions). The missing piece is the *web UI* so steps can be done from his phone. Ship 6 + Ship 7 deliver this.

**Three new feature asks (Phase 2, post-deploy):**

**R6. Company / JD / persona analysis brain.** For any company/job/person, AI extracts a structured analysis:
- Company: what they do, recent signals, product
- JD: must-have skills, level, YoE required, urgency cues
- Person: role, seniority, vibe (formal vs warm DM)
Triggered manually (paste text/URL/screenshot).

**R7. Multi-resume + AI resume tailoring per job.** Resume engine:
- Store multiple resume variants (PM, BA, Product Ops, APM, etc.) with markdown body + skill tags
- Given a JD, AI proposes targeted edits to a chosen variant (not a rewrite — bullet-level tweaks to surface JD keywords)
- User reviews each suggestion; never auto-applies
- Goal: "if they want an Associate PM, surface an APM-flavored version of my resume"

**R8. "Multiple brains" composition.** Each analysis (R6's company/JD/persona) is a distinct AI call ("brain"); their outputs assemble into the job card. e.g., open Presolv360's card → see Company Brain output + JD Brain output + Persona Brain output for each contact + Resume Brain recommendation, all in one screen.

**FDE note:** R6–R8 are powerful but heavy. They depend on Ship 5 (Anthropic API integration) AND on Ship 6+7 (web app to surface the structured output) being live first. Trying to build them before deploy = no deploy ever. Plan keeps them as Phase 2.

**For NOW (before Ship 5 API key arrives):** Claude-in-this-chat is the manual stand-in for R6/R7/R8. User pastes data → Claude extracts → Claude runs `tracker.py` commands to update DB. Works but doesn't scale to volume; that's why Ship 5 matters.

### Session 8 — (waiting)
Once Ship 6 Phase A is on localhost + Ship 7 is deployed, return to validate the live URL against the original Session 6 Phase 1 charter. Then start Sprint 3 (Ship 5 AI).
