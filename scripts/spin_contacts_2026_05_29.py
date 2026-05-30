"""Spin 2026-05-29 part 2: seed named recruiter contact(s) surfaced by JD.

Xurrent PM JD had the recruiter explicitly named with LinkedIn profile URL
(Vijayalakshmi R). No Apify scrape needed for that one — direct insert,
auto-gen outreach via outreach_gen.

Other new companies (E2M, Bajaj Finserv Health, Itron, SOTI, etc.) need a
separate LinkedIn company-employees scrape if/when the user approves cost.
"""
import sys
from datetime import datetime, timezone
sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402
import outreach_gen as og  # noqa: E402

USER_ID = 1


def s(v):
    return "" if v is None else str(v)


# (slug, name, role_label, company_key, contact_type, priority, seniority, about)
PEOPLE = [
    ("vijayalakshmir1910", "Vijayalakshmi R", "Recruiter @ Xurrent",
     "Xurrent", "recruiter", 1, "Recruiter",
     "Recruiter at Xurrent (B2B SaaS ITSM/ITAM). Named directly on Product Manager JD as point of contact."),
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        jobs = conn.execute(
            "SELECT id, company, title FROM jobs WHERE user_id=? AND status='discovered'",
            (USER_ID,),
        ).fetchall()
    company_to_job = {}
    for j in jobs:
        c = (j["company"] or "").lower().strip()
        if c == "xurrent":
            company_to_job.setdefault("Xurrent", (j["id"], j["title"]))
    print("Company -> Job resolution:")
    for k, v in company_to_job.items():
        print(f"  {k} -> job_id={v[0]}, title='{v[1]}'")

    ins = dup = 0
    with get_connection() as conn:
        for (slug, name, role, company_key, ctype, prio, sen, about) in PEOPLE:
            if company_key not in company_to_job:
                print(f"  [skip] {name}: no matching job for {company_key}")
                continue
            job_id, job_title = company_to_job[company_key]
            url = f"https://in.linkedin.com/in/{slug}"
            if conn.execute(
                "SELECT id FROM contacts WHERE user_id=? AND job_id=? AND linkedin_url LIKE ?",
                (USER_ID, job_id, f"%{slug}%"),
            ).fetchone():
                dup += 1
                continue
            msgs = og.generate(name, ctype, job_title, company_key)
            if len(msgs["connect_note"]) > 200:
                msgs["connect_note"] = msgs["connect_note"][:197] + "..."
            conn.execute(
                "INSERT INTO contacts (user_id, job_id, name, role, linkedin_url, "
                "connect_note, followup_msg, inmail_subject, inmail_body, "
                "contact_type, priority, seniority, about, added_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, job_id, s(name), s(role), url,
                 msgs["connect_note"], msgs["followup_msg"],
                 msgs["inmail_subject"], msgs["inmail_body"],
                 ctype, prio, sen, s(about), now),
            )
            ins += 1
        conn.commit()
    print(f"\nContacts inserted: {ins}  Deduped: {dup}")


if __name__ == "__main__":
    main()
