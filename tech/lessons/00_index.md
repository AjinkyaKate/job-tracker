# Lessons Index

Each lesson is written **when we hit the concept in the build**, not all upfront. Order roughly follows the ship plan in `../../CLAUDE.md` §4.

When you reopen this folder after a gap and forget a concept, the lesson here is your refresher. Every lesson follows the template in `../persona_teacher.md`.

## Planned lessons

| # | Lesson | Triggered by |
|---|---|---|
| 01 | [`01_what_is_python.md`](01_what_is_python.md) — programming languages, why Python, how to run a script ✅ | Ship 0 |
| 02 | [`02_what_is_terminal_and_shell.md`](02_what_is_terminal_and_shell.md) — terminal, shell, prompt, navigating ✅ | Ship 0 |
| 03 | [`03_what_is_git.md`](03_what_is_git.md) — version control, commits, branches, GitHub ✅ | Ship 0 |
| 04 | [`04_what_is_venv.md`](04_what_is_venv.md) — virtual environments, pip, requirements.txt ✅ | Ship 0 |
| 05 | `05_python_basics.md` — variables, types, lists, dicts, functions, control flow | Ship 1 |
| 06 | `06_what_is_a_database.md` — tables, rows, SQL, SQLite | Ship 2 |
| 07 | `07_what_is_an_api.md` — HTTP, requests, JSON, status codes | Ship 3 prep |
| 08 | `08_what_is_an_llm_api.md` — prompts, tokens, structured output, Anthropic SDK | Ship 5 |
| 09 | `09_what_is_a_backend.md` — server, request/response cycle, FastAPI | Ship 11 |
| 10 | `10_what_is_a_frontend.md` — HTML, browser, HTMX, why not React (yet) | Ship 12 |
| 11 | `11_what_is_deployment.md` — hosting, environments, secrets, env vars | Ship 15 |
| 12 | `12_writing_good_code.md` — naming, function size, comments, structure | cross-cutting |
| 13 | `13_how_systems_connect.md` — end-to-end flow of a single user request | after Ship 11 |

## How lessons relate to tech-interview prep

Each finished lesson has a **"60-second interview-ready answer"** at the bottom. When you prep for a tech screen, re-read those sections — that's a compressed crash course.

Common tech-interview questions and the lesson that prepares you:

- "Explain how an API works" → `06_what_is_an_api.md`
- "Walk me through what happens when a user clicks 'submit'" → `12_how_systems_connect.md`
- "How would you store this data?" → `05_what_is_a_database.md`
- "What's the difference between frontend and backend?" → `08_what_is_a_backend.md` + `09_what_is_a_frontend.md`
- "Have you used LLM APIs in production?" → `07_what_is_an_llm_api.md`
