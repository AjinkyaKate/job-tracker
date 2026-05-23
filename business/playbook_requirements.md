# Playbook: Requirement Gathering

> The framework an FDE uses to turn vague pain into structured requirements.

This is *the* craft. Learn this loop and you can run it on any problem, any user, any interview.

## The 7-step loop

### Step 1 — Discover the user

**Goal:** know who you're building for as a real human, not a job title.

**Ask:**
- Who are you and what do you do day-to-day?
- Walk me through yesterday — what did you actually spend time on?
- Who do you work with? Who depends on you?
- What's your level of comfort with [the tools/tech in scope]?

**Why this first:** the same problem looks different for different users. A "messy job hunt" for a senior PM with 100 weekly applications is a different beast than for a college grad with 3.

---

### Step 2 — Find the pain

**Goal:** surface the *specific* things that hurt, with frequency and severity.

**Ask:**
- What's the most annoying part of [the activity]?
- When was the last time it went wrong? Walk me through.
- If you could wave a wand and fix one thing, what would it be?
- How much time does this cost you per week?

**Push back on abstractions.** "It's slow" — slow how? "It's manual" — what specifically is the manual step? You want concrete examples and numbers.

---

### Step 3 — Understand current workarounds

**Goal:** see what they do today and where it breaks.

**Ask:**
- How do you handle this today? Walk me through.
- What tools are you using — spreadsheets, notes apps, memory?
- When does the current setup fail? Most recent failure?

**Key insight:** if they already have a workaround (a hacky spreadsheet, a Notion page, a WhatsApp thread), the problem is real enough that they're solving it badly themselves. That's *strong* signal. No workaround? Maybe the pain isn't sharp enough yet.

---

### Step 4 — Define success

**Goal:** know what "done" looks like for *the user*, not for you.

**Ask:**
- Imagine this is solved 3 months from now. What does your day look like differently?
- What would you stop doing? What would you do more of?
- How would we both know it's working — what number changes?

**Concrete metrics beat vague satisfaction.** "I'd feel less stressed" → push to "I'd spend X hours less per week" or "my reply rate would go from Y% to Z%."

---

### Step 5 — Pin down scope (MoSCoW)

**Goal:** separate the few critical things from the many nice-to-haves.

**Categorize every candidate feature:**
- **Must have** — without this, the whole solution fails
- **Should have** — important but not blocking the first usable version
- **Could have** — nice if cheap, drop if hard
- **Won't have (now)** — explicitly out of scope, named so it doesn't sneak back in

**Why explicit "won't have":** unnamed scope creeps in. Named scope stays out.

---

### Step 6 — Validate

**Goal:** catch misunderstandings *before* you build the wrong thing.

**Do:**
- Read the requirements back: "So here's what I heard..."
- Walk through a fake scenario: "Tomorrow you get a LinkedIn DM about a PM role at Stripe. Walk me through how you'd use this thing." Watch for friction.
- Watch for "yes, but..." — every "but" is a hidden requirement you didn't capture yet
- Show a paper sketch or wireframe and ask what's missing

**Real talk:** people often agree in the room and disagree in practice. The scenario walkthrough is how you catch that.

---

### Step 7 — Document

**Goal:** produce an artifact someone else could build from cold.

**Structure** (see `requirements_v1.md` for the live version):
- User persona
- User stories — *As [role], I want [goal], so that [benefit]*
- Acceptance criteria per story — *how do we know it's done?*
- Non-functional requirements — speed, reliability, security, privacy
- Out of scope — explicit
- Open questions — what you still don't know

## Common traps to avoid

- **Solutioning too early.** "So you need a Kanban board" → no, they need to remember who they reached out to. Stay on the problem until requirements are clear.
- **The HiPPO trap** (Highest Paid Person's Opinion). Even when the user *is* the paying customer, watch for "I just want it to do X" without understanding why.
- **Confirmation bias.** Leading questions to get the answer you wanted. "You'd want auto-apply, right?" → bad. "How do you decide which jobs are worth applying to?" → good.
- **Skipping validation.** Building from your interpretation without playing it back.
- **Falling for vanity features.** The shiny AI feature is fun. The boring "remind me to follow up" is what actually saves the user.

## Bridge to PM interview frameworks

This 7-step loop is the underlying machinery. Named PM frameworks are just packaging:

- **CIRCLES** (Comprehend, Identify, Report, Cut, List, Evaluate, Summarize) — popular for "design a product" questions
- **AARM** (Acquisition, Activation, Retention, Monetization) — for product-strategy questions
- **JTBD** (Jobs To Be Done) — for "why do customers hire your product"

They all rest on: *discover → pain → success → scope → validate → document*. Master the loop and the framework names are just vocabulary.

## How to run a session

A single requirement-gathering session usually covers 1–3 steps deeply, not all 7 shallowly. Better to fully understand pain than to half-skim all 7 steps. Iterate across sessions.

Every session ends by **appending to `requirements_v1.md`** — both the questions asked and the answers given. The folder becomes self-documenting.
