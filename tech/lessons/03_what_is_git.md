# Lesson 03 — What is Git?

> Triggered by: Ship 0 first commit. Time to read: ~6 min.

## In one sentence

**Git is a time machine for your code** — it saves labeled snapshots of your project so you can see what changed, when, and roll back if you break things.

## A real-world analogy

Imagine writing a long document. Without version control, you'd save copies: `report_v1.docx`, `report_v2_final.docx`, `report_v2_final_REAL.docx`, `report_v2_final_REAL_USE_THIS.docx`. You've seen this folder. So have I.

Git is the proper version of that. Instead of multiple files cluttering your desktop, **ONE folder** holds your latest version, AND every prior version is stored in a hidden `.git` subfolder. You can ask: "show me what this looked like a week ago" or "undo yesterday's change" without losing today's work.

Git is also how teams collaborate. Two people edit different parts of the same code, git merges them. (We're solo for now, but the habit matters from day 1.)

## Where this shows up in our project

- After every meaningful change ("Ship 0 done", "Ship 1 list command works", "fixed contact bug"), you save a **commit** — a labeled snapshot.
- The whole project, with its full history, lives in a folder called a **repository** (repo for short). The repo is just your normal folder + a hidden `.git/` subfolder where the history is stored.
- Later: you'll push the repo to **GitHub** so it lives in the cloud and is shareable / backed up.

## The minimum you need to know

### Three states a file can be in
1. **Modified** — you changed it on disk, but git hasn't been told yet
2. **Staged** — you said "include this in the next snapshot" (via `git add`)
3. **Committed** — git wrote a permanent snapshot to the history (via `git commit`)

It's a two-step pattern on purpose: stage what you want, then commit. Lets you snapshot only *some* of your changes if you've been working on multiple things.

### The 5 commands you'll use 95% of the time

| Command | What it does |
|---|---|
| `git status` | What's changed? What's staged? Always your first move when unsure. |
| `git add <file>` | Stage a file for the next commit. Use `.` to stage everything changed. |
| `git commit -m "message"` | Take a snapshot of staged files, label it with the message |
| `git log` | Show the project's commit history |
| `git diff` | Show me the actual lines that changed |

### A commit needs three things

- **Your name** (so history says who did it)
- **Your email** (same reason; also used by GitHub to associate commits to your account)
- **A message** (a short label describing what changed)

The name + email are set **once per machine**, with:
```
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

These get baked into every future commit you make on this machine. Use real, stable info — the same name and email you'd want associated with your work publicly.

### The `.gitignore` file

A plain-text file listing things git should **pretend don't exist** — never tracked, never committed. We never want to commit:
- **Secrets** — `.env` with API keys would leak you on GitHub
- **Generated junk** — `__pycache__/`, `*.pyc` (Python's compiled cache)
- **Big binary files** — databases (`tracker.db`), media files
- **Editor leftovers** — `.DS_Store` on Mac, `.idea/` from JetBrains, etc.

Set this up Day 1. Adding a file to `.gitignore` after it's been committed once is painful.

## A worked example — the commands you'll run shortly

```
# 1. Tell git who you are (one-time per machine)
git config --global user.name "Ajinkya Kate"
git config --global user.email "you@example.com"

# 2. Initialize the repo (creates the hidden .git/ folder)
git init

# 3. See what git sees
git status
# → "Untracked files: tracker.py, CLAUDE.md, ..." etc.

# 4. Stage everything
git add .

# 5. Make the first commit
git commit -m "Ship 0: project skeleton, first Python file runs"

# 6. See the result
git log
# → one entry, your first commit
```

## Check yourself

- What's the difference between **staged** and **committed**?
- Why don't we commit `.env` files?
- What does `git status` answer?
- If you've been editing 3 files but only want to commit 2 of them right now, what's the workflow?

## Interview-ready 60-second answer

*"Git is the standard version-control system. It tracks file changes as a graph of commits — each commit being a labeled snapshot of the project. Day-to-day, the cycle is: edit, `git add` to stage, `git commit -m` with a message. For collaboration, branches let multiple people work in parallel and `git merge` brings the work back together. Used in nearly every modern software project. GitHub is a separate thing — it's a hosting service for git repositories that adds collaboration features like pull requests."*

## Open threads

- **Branches and merging** — for parallel work; comes up when projects grow
- **Pull requests** — branches + review; how teams ship code together
- **GitHub vs Git** — Git is the tool; GitHub is the hosting service. We'll set up GitHub later in Ship 0.
- **Reverting and resetting** — undoing changes; learn when you need it
- **`.gitignore` patterns** — globs (`*.pyc`, `**/*.log`); learn as you write them
