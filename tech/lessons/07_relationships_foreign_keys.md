# Lesson 07 — Relationships between tables (foreign keys, JOINs)

> Triggered by: Ship 3 (adding contacts linked to jobs). Time to read: ~10 min, reference doc.

## In one sentence

A **foreign key** is a column in one table that "points to" a row in another table — that's how you represent relationships like *"this job has many contacts"* without duplicating data.

## A real-world analogy

Back to the filing cabinet (Lesson 06). You now have:

- **Jobs drawer** — one folder per job
- **Contacts drawer** — one folder per contact

Each contact folder has a small sticky note on it: *"belongs to Job #1"*. That sticky note is the **foreign key** — a label that says which job the contact is attached to.

Krunal's contact folder has *"belongs to Job #1"*. Latika's contact folder also has *"belongs to Job #1"*. Both link to the same Presolv360 job. That's a **one-to-many relationship** — one job has many contacts.

The cabinet enforces a rule: every sticky note must point to a real job folder. You can't make a contact for nonexistent Job #999. That rule is the **foreign key constraint**.

## Where this shows up in our project

Ship 3 adds a `contacts` table with a `job_id` column that references `jobs.id`:

```sql
CREATE TABLE contacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    role TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    notes TEXT,
    added_at TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

Your Presolv360 lead (Job #1) now has TWO contact rows:
- Krunal Modi (Founding Member & Chief of Staff)
- Latika Gehlot (HR Director, with her email + phone)

Both rows in `contacts` have `job_id = 1`. The notes field on the job no longer has to be a graveyard for contact info.

## The minimum you need to know

### 1. One-to-many: where does the FK live?

**The "many" side holds the foreign key.** One job has many contacts → the `job_id` column goes on `contacts`, not on `jobs`.

Why? If you put a `contact_ids` column on `jobs`, you'd need a list there — but SQL columns hold single values, not lists. The standard pattern is: put one column on the many side, pointing back to the one side.

### 2. FOREIGN KEY syntax

```sql
FOREIGN KEY (job_id) REFERENCES jobs(id)
```

Reading: *"the value in `contacts.job_id` must match an existing value in `jobs.id`."*

If you try `INSERT INTO contacts (job_id, name) VALUES (999, 'Bob')` and no job #999 exists, the database refuses (when foreign keys are enforced — see next point).

### 3. SQLite foreign keys are OFF by default

A quirk of SQLite for historical reasons: foreign key constraints exist in the schema but aren't actually enforced unless you turn them on **per connection**:

```python
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn
```

This single PRAGMA line is the difference between "FK rules in schema, ignored in practice" and "FK rules enforced." Postgres and MySQL enforce by default; SQLite doesn't. Always include the pragma.

### 4. JOINs — combining data across tables

When you want both job info AND contact info in one query, you JOIN:

```sql
SELECT
    j.id, j.title, j.company, j.status,
    c.name AS contact_name, c.role, c.email, c.phone
FROM jobs j
LEFT JOIN contacts c ON c.job_id = j.id
ORDER BY j.id, c.id;
```

Reading:
- `FROM jobs j` — start with the jobs table, give it the short alias `j`
- `LEFT JOIN contacts c ON c.job_id = j.id` — attach matching rows from contacts (aliased `c`), where their `job_id` equals the job's `id`
- One row in the output per (job, contact) combo. A job with 2 contacts produces 2 result rows.

### 5. LEFT JOIN vs INNER JOIN

- **INNER JOIN** — only rows where there's a match in *both* tables. A job with zero contacts disappears from the result. Bad default.
- **LEFT JOIN** — all rows from the left table, with NULLs filled in if there's no match. A job with zero contacts shows up with NULL contact columns. Safer default.

**Rule of thumb:** start with LEFT JOIN. Switch to INNER only when you specifically need to exclude unmatched rows.

## A worked example — Ship 3's enhanced `list`

Our actual code uses a different approach — **two queries, grouped in Python** — instead of a JOIN. Here's why:

A JOIN that pulls jobs with their contacts produces *one row per contact*, with the job columns repeated:

```
job_id | title    | contact_name | role
   1   | PM / PO  | Krunal Modi  | Founding Member
   1   | PM / PO  | Latika G.    | HR Director
   2   | PM lead  | Shailesh T.  | AI PM
```

That's awkward to format as a job header with contacts indented underneath. Easier: pull jobs separately, pull contacts separately, group in Python:

```python
def list_jobs():
    init_db()
    with get_connection() as conn:
        jobs = conn.execute("SELECT * FROM jobs ORDER BY id").fetchall()
        contacts = conn.execute(
            "SELECT * FROM contacts ORDER BY job_id, id"
        ).fetchall()

    contacts_by_job = {}
    for c in contacts:
        contacts_by_job.setdefault(c["job_id"], []).append(c)

    for job in jobs:
        print(f"  [{job['id']}] {job['title']} @ {job['company']}")
        for c in contacts_by_job.get(job["id"], []):
            print(f"          → {c['name']} ({c['role']})")
```

**Both approaches are valid.** JOIN is more SQL-elegant; two-queries-grouped is easier to format for tree-style output. Pick by readability for the use case.

## Check yourself

- Why does `job_id` go on the contacts table, not on the jobs table?
- What happens if you try to add a contact with `job_id = 999` when no such job exists, and the FK pragma is ON?
- What's the difference between LEFT JOIN and INNER JOIN? Which is the safer default?
- Why does SQLite need `PRAGMA foreign_keys = ON` per connection?
- If you wanted *all jobs that have a contact whose email contains "@gmail.com"*, what kind of query would you write?

## Interview-ready 60-second answer

*"Relational databases avoid duplicating data by splitting it across tables linked by foreign keys. A one-to-many relationship — one user has many orders — puts the FK on the many side (orders.user_id). JOINs combine data across tables; LEFT JOIN is the safe default because it preserves rows from the left table even when no match exists on the right. Schema design — what tables, what relationships — is often the most important early decision, because once data is in production you can't reshape it without migrations. In SQLite specifically, foreign keys are enforced only when you set `PRAGMA foreign_keys = ON` per connection — a known historical quirk."*

## Open threads

- **Many-to-many** — when both sides have multiple of the other (users ↔ roles). Needs a third "junction" table. Not in our scope.
- **ON DELETE CASCADE** — auto-delete child rows when parent is deleted. e.g., delete a job → its contacts vanish too. We're not using this yet (we'll keep contacts when jobs are deleted, defensively).
- **Indexes on FK columns** — speed up JOINs at scale. Not needed until tables are big.
- **Self-referencing FKs** — when a table references itself (org chart: `employee.manager_id` → `employee.id`).
- **JOIN types we didn't cover** — RIGHT JOIN (mirror of LEFT, rarely needed), FULL OUTER JOIN (both directions, SQLite doesn't have it directly).
- **Database normalization** — the broader theory of "split data into the right tables." Lookup *normal forms* if you want the academic version.
