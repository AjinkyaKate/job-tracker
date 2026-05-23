# Lesson 05 — Python Basics (a tour of tracker.py)

> Triggered by: Ship 1 (the real tracker.py). Time to read: ~15 min, but it's a reference — scan it once, return when stuck.

This lesson walks through `tracker.py` from top to bottom. Each section names what it does, the Python concepts it introduces, and *why* it's written this way. Read alongside the actual file open in Cursor.

---

## Section 1 — Imports (top of the file)

```python
import json
import os
import sys
from datetime import datetime
```

**What it does:** loads four pieces of code from Python's standard library so we can use them.

**Concept — `import`:** Python comes with hundreds of built-in modules ("a module" = a file full of useful functions). You don't get them automatically; you `import` only what you need.

- `json` — convert between Python data and JSON text (for saving to a file)
- `os` — operating system helpers; we use `os.path.exists` to check if a file is there
- `sys` — system-level stuff; we use `sys.argv` to read command-line arguments and `sys.exit` to quit with a code
- `from datetime import datetime` — slightly different: import just the `datetime` class *from* the `datetime` module. (Yes, both are called datetime. Python.)

**Style:** stdlib imports first, alphabetized. Project-specific imports go below, separated by a blank line.

---

## Section 2 — Constants

```python
JOBS_FILE = "jobs.json"
```

**Concept — variables:** a variable is a name that holds a value. `JOBS_FILE` is a variable; its value is the string `"jobs.json"`.

**Why ALL CAPS:** convention. ALL CAPS names = constants (values that never change once set). Lowercase names = regular variables. Python doesn't enforce this — it's a signal to other readers (and future-you).

**Why a constant here:** the filename appears in two functions (load + save). If we hardcoded `"jobs.json"` in both places, changing it later means two edits. With a constant, one edit.

---

## Section 3 — Functions: `load_jobs()` and `save_jobs()`

```python
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE) as f:
        return json.load(f)


def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)
```

**Concept — functions (`def`):** a function is a named, reusable block of code. `def load_jobs():` defines one called `load_jobs` that takes no arguments. `def save_jobs(jobs):` takes one argument called `jobs`.

You *call* a function with parentheses: `load_jobs()`.

**Concept — `if not ...`:** a basic conditional. `os.path.exists(JOBS_FILE)` returns `True` or `False`. `not` flips it. So this reads: *"if the file does not exist, return an empty list."*

**Concept — empty list `[]`:** Python lists are ordered collections. `[]` is an empty one. We return an empty list when there are no jobs yet, so the rest of the code doesn't crash on "no file."

**Concept — `with` block (context manager):** `with open(...) as f:` opens the file and assigns it to `f`. When the indented block ends, Python automatically closes the file — even if an error happens. Without `with`, you'd need to call `f.close()` yourself and risk leaving files open if something fails.

**Concept — `json.load(f)` and `json.dump(jobs, f, indent=2)`:** the `json` module converts:
- `json.load(f)` — reads JSON text from a file and gives you a Python list/dict
- `json.dump(jobs, f)` — writes a Python list/dict to a file as JSON text
- `indent=2` — pretty-prints with 2-space indentation so the file is human-readable

**Concept — `"w"` mode:** when opening a file, the second argument is the *mode*. Default is `"r"` (read). `"w"` is *write* — creates the file if missing, overwrites if exists.

---

## Section 4 — `add_job()`: the interactive prompt

```python
def add_job():
    jobs = load_jobs()
    new_id = len(jobs) + 1

    print(f"\nAdd job (id will be {new_id}). Press Enter to skip a field.\n")
    job = {
        "id": new_id,
        "title": input("  Job title: ").strip(),
        "company": input("  Company: ").strip(),
        "link": input("  Link: ").strip(),
        "status": input("  Status [saved]: ").strip() or "saved",
        "notes": input("  Notes: ").strip(),
        "added_at": datetime.now().isoformat(timespec="seconds"),
    }

    jobs.append(job)
    save_jobs(jobs)
    print(f"\nSaved as job #{new_id}: {job['title']} @ {job['company']}\n")
```

**Concept — dictionaries `{...}`:** the `job = {...}` block creates a **dictionary** — a collection of *key-value* pairs. Each entry has a key (a string in quotes) and a value.

So `job["title"]` looks up the value at key `"title"`. Real-world analogy: a phone's contact entry — name, phone, email are all keys; their actual values are what you stored.

**Concept — `input(...)`:** pauses the program, shows a prompt to the user in the terminal, waits for them to type something and press Enter, and returns what they typed as a string. This is how interactive CLIs work.

**Concept — `.strip()` on strings:** removes whitespace from the start and end of a string. If the user accidentally types `" Stripe "`, we want `"Stripe"`. Tiny but important.

**Concept — `or` for defaults:**

```python
input("  Status [saved]: ").strip() or "saved"
```

In Python, an empty string `""` is treated as "falsy" — like `False`. The `or` operator says: *use the left side if truthy; otherwise use the right side.*

So: if the user types something, use that. If they press Enter (empty string), fall back to `"saved"`. This is a slick way to provide defaults.

**Concept — `len(jobs)`:** returns the count of items in a list. We use `len(jobs) + 1` to generate a simple sequential ID. (Not perfect — if we ever delete jobs, IDs could collide. We'll fix this later when we add delete.)

**Concept — `f-strings`:** strings prefixed with `f` like `f"...{variable}..."`. The `{...}` part is replaced with the value of the variable. So `f"Saved as job #{new_id}"` becomes `"Saved as job #1"`. Much cleaner than the old `"..." + str(new_id)`.

**Concept — `jobs.append(job)`:** lists have an `.append()` method that adds an item to the end. After this line, our list is one longer.

**Concept — `datetime.now().isoformat(timespec="seconds")`:** asks Python for the current date+time, then formats it as a clean string like `"2026-05-23T22:15:30"`. Saved as a record of when this job entry was created.

---

## Section 5 — `list_jobs()`: the table view

```python
def list_jobs():
    jobs = load_jobs()
    if not jobs:
        print("\nNo jobs yet. Add one with: python3 tracker.py add\n")
        return

    print(f"\n{len(jobs)} job(s):\n")
    for job in jobs:
        print(f"  [{job['id']:>3}] {job['status']:<12}  {job['title']}  @  {job['company']}")
        if job.get("link"):
            print(f"        {job['link']}")
    print()
```

**Concept — `if not jobs:`:** an empty list is also "falsy" in Python. So `if not jobs:` is a tidy way to say "if the list is empty." Then `return` exits the function early.

**Concept — `for` loops:** `for job in jobs:` iterates over the list, giving you each item one at a time as `job`. Standard Python rhythm.

**Concept — fancy f-string formatting:** `{job['id']:>3}` means *right-align in 3 characters*. `{job['status']:<12}` means *left-align in 12 characters*. Used to produce a neat aligned table.

**Concept — `job.get("link")`:** safer than `job["link"]`. The `.get()` method returns `None` (Python's "no value") if the key doesn't exist, instead of crashing. We use it because old jobs in the file might not have a `link` field if we ever add new fields later.

---

## Section 6 — `usage()` and `main()`: the CLI plumbing

```python
def usage():
    print("Usage: python3 tracker.py <command>")
    print("Commands:")
    print("  add    Add a new job (interactive prompts)")
    print("  list   Show all saved jobs")


def main():
    if len(sys.argv) < 2:
        usage()
        sys.exit(1)

    command = sys.argv[1]
    if command == "add":
        add_job()
    elif command == "list":
        list_jobs()
    else:
        print(f"Unknown command: {command}\n")
        usage()
        sys.exit(1)
```

**Concept — `sys.argv`:** when you run `python3 tracker.py add`, Python gives you `sys.argv` as a list: `["tracker.py", "add"]`. The first item is always the script name; everything after is what the user typed.

So `sys.argv[1]` is the first argument they passed (`"add"` or `"list"`).

**Concept — `sys.exit(1)`:** exits the program. The number is a status code — `0` means success, anything else means error. Shell scripts use this to know if a command succeeded.

**Concept — `if/elif/else`:** standard branching. Try each condition in order; run the first matching block. `elif` is short for "else if."

---

## Section 7 — The `if __name__ == "__main__":` idiom

```python
if __name__ == "__main__":
    main()
```

**What it does:** runs `main()` only when this file is executed directly (`python3 tracker.py`), not when it's imported by another file.

**Why:** later we may want to import functions from `tracker.py` into other files (tests, other scripts). When you `import tracker`, Python runs every top-level statement in the file. Without this guard, importing would *automatically run* `main()`, which we don't want.

`__name__` is a special variable Python sets:
- `"__main__"` when you run the file directly
- `"tracker"` (the filename) when something else imports it

Standard idiom. You'll see it in nearly every Python script.

---

## Concepts you've now seen, in one place

| Concept | Example from our code |
|---|---|
| `import` | `import json` |
| Variables / constants | `JOBS_FILE = "jobs.json"` |
| Functions (`def`) | `def add_job():` |
| Function arguments | `def save_jobs(jobs):` |
| `if / elif / else` | `if command == "add":` |
| `not` for boolean negation | `if not jobs:` |
| Lists `[...]` and `.append()` | `jobs.append(job)` |
| `len()` on lists | `len(jobs) + 1` |
| Dictionaries `{...}` and `dict[key]` | `job["title"]` |
| `.get(key)` for safe access | `job.get("link")` |
| `for` loops | `for job in jobs:` |
| Strings and `.strip()` | `input(...).strip()` |
| `or` for default values | `... or "saved"` |
| f-strings | `f"Saved as job #{new_id}"` |
| f-string alignment | `{job['status']:<12}` |
| `input()` | `input("  Job title: ")` |
| `print()` | `print(...)` |
| `with open(...) as f:` | reading + writing files safely |
| `json.load` / `json.dump` | `json.load(f)` |
| `sys.argv` | `command = sys.argv[1]` |
| `sys.exit(code)` | `sys.exit(1)` |
| `if __name__ == "__main__":` | entry-point guard |

That's a lot. You don't need to memorize it — you need to know where to look it up.

---

## Check yourself

- What's the difference between a **list** and a **dictionary**? When would you use each?
- What does `with open(...) as f:` give you that plain `open()` doesn't?
- Why is `if __name__ == "__main__":` at the bottom of the file?
- If you ran `python3 tracker.py foo`, what would happen and why?
- In the line `input("...").strip() or "saved"`, why does the `or "saved"` fall back to `"saved"` when the user just presses Enter?

## Interview-ready 60-second answer

*"Python has a small set of core concepts you'll use 95% of the time: variables, functions, conditionals, loops, lists, and dictionaries. Files are read/written safely using `with` blocks (context managers). Modules from the standard library — `json`, `os`, `sys`, `datetime` — handle most common needs without external dependencies. Command-line scripts use `sys.argv` for arguments and the `if __name__ == '__main__':` idiom as the entry point. f-strings are the modern way to build strings with embedded variables. With those concepts you can write practical scripts; everything else — classes, async, decorators, generators — is layered on top."*

## Open threads

- **Classes and objects** — when you want to bundle data + behavior together (e.g., a `Job` class). We've kept it dict-based for now; classes come later when complexity demands them.
- **Exception handling (`try / except`)** — what happens when input is bad or files are corrupted. Phase 2 work.
- **`argparse`** — Python's real library for command-line argument parsing. `sys.argv` is the manual way; `argparse` adds help text, type checking, default values. We'll graduate to it when our CLI grows past 4–5 commands.
- **Type hints** — Python's optional way to declare what type a variable or argument is (`def add_job() -> None:`). Useful in larger codebases.
