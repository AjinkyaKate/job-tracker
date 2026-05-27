"""Copy locally-scraped Discover data (jobs + contacts) into the prod Postgres.

SAFETY:
- Reads the prod connection string from PROD_DATABASE_URL (a DISTINCT var, set
  in a gitignored .env.prod). It is NOT named DATABASE_URL, so the running local
  webapp / MCP keep using SQLite and never accidentally point at prod.
- Source = local tracker.db (read directly via sqlite3). Dest = prod Postgres.
- Only migrates status='discovered' jobs + their contacts. Leaves prod's own
  Gmail-sourced leads / pipeline untouched. Dedups by (user_id, link).
- Run WITHOUT TARGET_USER_ID first: it just prints prod users + counts (inspect).
  Then re-run with TARGET_USER_ID=<id> to actually write.

Usage:
  set -a; . .env.prod; set +a            # loads PROD_DATABASE_URL into env
  python scripts/migrate_discover_to_prod.py                 # inspect
  TARGET_USER_ID=2 python scripts/migrate_discover_to_prod.py  # migrate
"""
import os
import sys
import sqlite3

PROJECT = "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker"
LOCAL_DB = os.path.join(PROJECT, "tracker.db")

prod = os.environ.get("PROD_DATABASE_URL")
if not prod:
    sys.exit("ERROR: PROD_DATABASE_URL not set. Put it in .env.prod and run:\n"
             "  set -a; . .env.prod; set +a")

# Point db.py at prod BEFORE importing it.
os.environ["DATABASE_URL"] = prod
sys.path.insert(0, PROJECT)
import db        # noqa: E402  (now IS_POSTGRES=True -> connects to prod)
import tracker   # noqa: E402

JOB_COLS = ["title", "company", "link", "location", "company_size",
            "company_industry", "company_url", "work_arrangement", "comp_range",
            "level", "yoe_required", "posted_at", "source", "jd_summary",
            "must_have_skills", "jd_raw_text", "ai_score", "ai_score_reason",
            "status", "added_at"]
CONTACT_COLS = ["name", "role", "email", "phone", "linkedin_url", "notes",
                "connect_note", "followup_msg", "contact_type", "priority",
                "seniority", "about", "added_at"]


def col(row, name):
    return row[name] if name in row.keys() else None


def main():
    src = sqlite3.connect(LOCAL_DB)
    src.row_factory = sqlite3.Row
    jobs = src.execute(
        "SELECT * FROM jobs WHERE user_id = 1 AND status = 'discovered'"
    ).fetchall()
    contacts_by_job = {
        j["id"]: src.execute(
            "SELECT * FROM contacts WHERE user_id = 1 AND job_id = ?", (j["id"],)
        ).fetchall() for j in jobs
    }
    n_contacts = sum(len(v) for v in contacts_by_job.values())
    print(f"LOCAL: {len(jobs)} discovered jobs, {n_contacts} contacts to migrate.")

    target = os.environ.get("TARGET_USER_ID")

    with db.get_connection() as conn:
        users = conn.execute("SELECT id, email, name FROM users ORDER BY id").fetchall()
        prod_disc = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE status = 'discovered'"
        ).fetchone()["n"]
    print(f"PROD: {len(users)} user(s), {prod_disc} discovered jobs currently.")
    for u in users:
        print(f"   user_id={u['id']}  {u.get('email')}  {u.get('name')}")

    if not target:
        print("\nINSPECT ONLY. Re-run with TARGET_USER_ID=<id> to migrate.")
        return

    target = int(target)
    print(f"\nMigrating to prod user_id={target} ...")
    tracker.init_db()  # ensure prod has the new contact columns

    ins_j = ins_c = dup = 0
    with db.get_connection() as conn:
        for j in jobs:
            if conn.execute(
                "SELECT id FROM jobs WHERE user_id = ? AND link = ?",
                (target, j["link"]),
            ).fetchone():
                dup += 1
                continue
            vals = [col(j, c) for c in JOB_COLS]
            new_id = db.insert_returning_id(
                conn,
                "INSERT INTO jobs (user_id," + ",".join(JOB_COLS) + ") VALUES ("
                + ",".join(["?"] * (len(JOB_COLS) + 1)) + ")",
                [target] + vals,
            )
            ins_j += 1
            for c in contacts_by_job[j["id"]]:
                cvals = [col(c, k) for k in CONTACT_COLS]
                conn.execute(
                    "INSERT INTO contacts (user_id,job_id," + ",".join(CONTACT_COLS)
                    + ") VALUES (" + ",".join(["?"] * (len(CONTACT_COLS) + 2)) + ")",
                    [target, new_id] + cvals,
                )
                ins_c += 1
        conn.commit()

    print(f"DONE. Jobs inserted: {ins_j} (deduped {dup}). Contacts inserted: {ins_c}.")
    with db.get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? AND status = 'discovered'",
            (target,),
        ).fetchone()["n"]
    print(f"PROD discovered jobs for user {target} now: {total}")


if __name__ == "__main__":
    main()
