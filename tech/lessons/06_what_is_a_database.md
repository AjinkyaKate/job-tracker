# Lesson 06 — Databases & SQL (with SQLite)

> Triggered by: Ship 2 (replacing jobs.json with tracker.db). Time to read: ~12 min, reference doc — scan once, return when stuck.

## In one sentence

A **database** is structured, persistent storage for your data — think of it as a spreadsheet that programs can read and write to, with strict rules about what goes where.

## A real-world analogy — the filing cabinet

Imagine a metal filing cabinet:

- **The cabinet itself** = the database
- **Each drawer** = a *table* (one drawer labeled "Jobs," another "Contacts," another "Messages")
- **Each folder inside a drawer** = a *row* (one folder per job, one per contact, etc.)
- **The labels on each folder** (Title, Company, Status...) = *columns*

When you ask the cabinet, *"Give me every folder from the 'Jobs' drawer where the Status label says 'applied'"* — that's a SQL query. The cabinet hands you back just those folders, fast.

A `jobs.json` file (what we had in Ship 1) is like dumping every paper on the floor and trying to sort through them. Works for ten papers. Falls apart at a hundred. A real cabinet (database) stays organized, fast, and consistent — even at millions of rows.

## Where this shows up in our project

Ship 2 replaces `jobs.json` with `tracker.db` — a single SQLite file. The `add` and `list` commands work exactly the same from your side. Under the hood, instead of loading the whole JSON file every time, we run targeted SQL queries that hit only the rows we need.

Why this matters going forward:
- **Ship 3 (contacts):** new `contacts` table, linked to `jobs` via a foreign key (one job → many contacts)
- **Ship 4 (messages):** new `messages` table, linked to `contacts`
- **Filtering:** "show me only jobs in status `awaiting_hr_review`" becomes a one-line SQL query
- **Sorting, counting, joining:** trivial with SQL; painful in JSON

You can't grow the tracker's data model without a real database. Ship 2 is the foundation everything later sits on.

## The minimum you need to know

### 1. The four core SQL operations

You'll spend 95% of your SQL time on these:

| Verb | Purpose | Example |
|---|---|---|
| `SELECT` | Read rows | `SELECT * FROM jobs WHERE status = 'applied'` |
| `INSERT` | Create a new row | `INSERT INTO jobs (title, company) VALUES ('PM', 'Stripe')` |
| `UPDATE` | Modify existing rows | `UPDATE jobs SET status = 'interview' WHERE id = 3` |
| `DELETE` | Remove rows | `DELETE FROM jobs WHERE id = 3` |

SQL keywords are usually written in CAPS by convention. Tables and columns are lowercase.

### 2. SQLite specifically

- **File-based.** The entire database lives in one file (`tracker.db`). No server to start, no port to configure. Copy the file = back up the data.
- **Built into Python.** The `sqlite3` module is part of the standard library — no `pip install` needed.
- **Single-writer.** Only one process can write at a time. Fine for our solo CLI; not for a high-traffic web app (we'll move to Postgres in Phase 4).
- **SQL dialect.** SQLite supports most standard SQL with some quirks; the basics are identical to Postgres/MySQL.

### 3. Schema — the structure of your tables

You define your tables once, with their columns and rules:

```sql
CREATE TABLE IF NOT EXISTS jobs (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    title      TEXT NOT NULL,
    company    TEXT,
    link       TEXT,
    status     TEXT NOT NULL DEFAULT 'saved',
    notes      TEXT,
    added_at   TEXT NOT NULL
);
```

Reading this:
- `CREATE TABLE IF NOT EXISTS jobs` — create a table called `jobs`; skip if it already exists. Safe to run every time the app starts.
- Each line = a column definition: `column_name TYPE [constraints]`
- **`INTEGER PRIMARY KEY AUTOINCREMENT`** — the `id` column is a number, uniquely identifies each row, and the database fills it in automatically when you insert (you never set it yourself)
- **`TEXT NOT NULL`** — must be a string, and it cannot be empty
- **`DEFAULT 'saved'`** — if you don't specify, status becomes `'saved'`

The schema enforces data integrity at the database layer. Even if a bug in our code tries to insert a job without a title, the database will refuse and raise an error. That's a feature.

### 4. Parameterized queries — non-negotiable

**Never** do this:

```python
# DON'T — this is how SQL injection vulnerabilities are born
conn.execute(f"INSERT INTO jobs (title) VALUES ('{user_input}')")
```

If `user_input` contains a `'`, the string breaks. Worse, if it contains malicious SQL (`'); DROP TABLE jobs; --`), an attacker just deleted your data.

**Always** do this:

```python
# DO — the database handles escaping safely
conn.execute(
    "INSERT INTO jobs (title) VALUES (?)",
    (user_input,)
)
```

The `?` is a placeholder. You pass the actual value as a *separate* tuple. The database substitutes it safely. Even though our tracker is single-user (no attackers), build the habit on day one. Production code without parameterized queries is a CVE waiting to happen.

### 5. The `with` block (we used it for files too)

```python
with get_connection() as conn:
    rows = conn.execute("SELECT * FROM jobs").fetchall()
```

Just like `with open(...) as f:`, this auto-closes the database connection (and commits any pending changes) when the block ends. Don't forget the commit otherwise — your changes won't be saved. The `with` block handles it.

## A worked example — the actual Ship 2 code

After Ship 2, `tracker.py` has these key pieces (read it in Cursor side-by-side):

**Schema definition (top of file):**
```python
SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    company TEXT,
    link TEXT,
    status TEXT NOT NULL DEFAULT 'saved',
    notes TEXT,
    added_at TEXT NOT NULL
);
"""
```

**Connection helper:**
```python
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn
```

`row_factory = sqlite3.Row` lets you access columns by name (like a dict) instead of by position. So `row["title"]` works, not just `row[1]`.

**Inserting a job:**
```python
with get_connection() as conn:
    cursor = conn.execute(
        "INSERT INTO jobs (title, company, link, status, notes, added_at) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (title, company, link, status, notes, added_at),
    )
    new_id = cursor.lastrowid
```

- The SQL string can span lines (Python concatenates adjacent string literals)
- The tuple of values matches the `?` count and order
- `cursor.lastrowid` gives back the auto-generated `id` — useful for telling the user "saved as #5"

**Reading all jobs:**
```python
with get_connection() as conn:
    rows = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
```

- `SELECT *` = all columns. (Use explicit column names in production code; * is fine for small projects.)
- `ORDER BY id` = sort by id (ascending by default)
- `.fetchall()` = pull all matching rows into a list at once

## Check yourself

- What's the difference between a **table** and a **row**?
- Why do we use `?` placeholders instead of f-strings to build SQL?
- What does `PRIMARY KEY AUTOINCREMENT` do for the `id` column?
- If you wanted to find all jobs whose status is `'applied'`, what SQL would you write?
- Why is the database file (`tracker.db`) in `.gitignore`?

## Interview-ready 60-second answer

*"Relational databases store data in tables of rows and columns; you query them with SQL. The four core verbs are SELECT, INSERT, UPDATE, DELETE. SQLite is file-based, embedded in Python's standard library, and great for development or single-user apps; Postgres is the typical production choice and uses the same SQL. Always use parameterized queries (`?` placeholders) instead of string-building to prevent SQL injection. The schema — what tables exist, what columns, what relationships — is often the most important design decision in an app, because once data is in production you can't easily change shape without migrations."*

## Open threads

- **Foreign keys** — how `contacts` will reference a `job_id`; comes in Ship 3
- **JOINs** — combining data across tables (e.g., "all jobs with their contacts' last messages"); Ship 4+
- **Indexes** — speed up queries on large tables by adding lookup structures; defer until something's slow
- **Migrations** — evolving the schema over time without losing data; a real topic in Phase 4 (when we move to Postgres on Supabase)
- **ORMs** (SQLAlchemy, Django ORM) — Python libraries that let you work with classes instead of raw SQL; deliberately not used here so you actually see SQL
- **SQLite vs Postgres** — same SQL mostly, but Postgres handles concurrent writes, is networked, scales further; we switch when we deploy
