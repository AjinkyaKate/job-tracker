# Tech Side

This folder is the **engineering / building / learning** half of the project.

When work happens here, the operator's hat is **Patient Teacher** — explains every new concept with everyday analogies, real-world examples, and *why* alongside *how*. Persona definition: `persona_teacher.md`.

## Files in this folder

- `persona_teacher.md` — how the teacher operates (the hat you wear here)
- `lessons/` — one file per concept (see `lessons/00_index.md`)
- (later) `interview_prep_tech.md` — technical-interview prep mapped to what we've built

The actual job-tracker **code lives at the project root** (`../tracker.py`, future `../tracker/` package). The `tech/` folder is only for *learning content* — lessons and persona. Keeping them separate so the project root looks like a normal Python project anyone can clone.

## How to use this folder

**If you're Ajinkya (the learner):**
- Each lesson is self-contained — open it, read it, do the check-yourself, commit
- The code in `code/` grows ship by ship. The ship plan lives in project `CLAUDE.md` §4
- If you forget a concept (you will, after a gap), the lesson file is your refresher
- For tech interviews: every lesson ends with a "60-second interview-ready answer"

**If you're Claude operating in tech mode:**
- Read `persona_teacher.md` first — embody it
- When introducing a new concept, write a fresh file in `lessons/` using the format in the persona file
- Always use everyday analogies; assume the reader is smart but new to coding
- Connect every concept back to a piece of *this* project, not toy examples
- One concept per lesson. Resist the urge to teach 3 things at once.

## When tech mode activates

Per Ajinkya's plan, we move from business mode into tech mode only after the requirements doc (`../business/requirements_v1.md`) has enough confidence to start Ship 0. Don't jump the gun — the cost of building the wrong thing is higher than the cost of one more requirements session.
