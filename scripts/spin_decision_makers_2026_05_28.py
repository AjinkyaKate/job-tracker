"""Spin 2026-05-28 part 2: decision-makers for the new companies.

Company-employees run IniafJUQR2KrDSLAP across 9 candidate companies. 4 slugs
resolved (Noise, Signzy, Eightfold, OfBusiness) → 10 clean decision-makers.
Other slugs (saleshandy, talentsavvy-software, farsighted-systems, skillzi,
kodofintech) returned noise — left for a manual slug-resolution pass.

For each contact: classify type + priority + seniority, snapshot about,
and auto-generate connect_note + InMail + follow-up via outreach_gen.
Idempotent: dedups by (job_id, linkedin_url).
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
    # Noise (Product Manager - B2C)
    ("gauravkhatrigonoise", "Gaurav Khatri", "CEO & Co-Founder @ Noise",
     "Noise", "founder", 3, "Founder/CEO",
     "CEO & co-founder of Noise, India's #1 smartwatch brand; consumer tech entrepreneur."),
    ("smeer-chopra", "Smeer Chopra", "CFO @ Noise",
     "Noise", "leader", 2, "CFO",
     "CFO at Noise; 30+ yrs in retail/e-commerce/FMCG/manufacturing; ex-Lenskart CFO."),
    ("p11akasha", "Akash Agarwal", "VP International @ Noise",
     "Noise", "leader", 2, "VP Intl",
     "VP International at Noise; global growth leader; ex-Dyson, Nestlé, Snapdeal; D2C/GTM."),
    # Signzy (Product Manager)
    ("ashishkumar-agarwal", "Ashishkumar Agarwal", "Enterprise Revenue Leader @ Signzy",
     "Signzy", "leader", 2, "Revenue Leader",
     "Leads enterprise revenue across BFSI at Signzy; 25 yrs, AI-led GTM, ex-Deloitte/IBM."),
    ("sanikagavankar", "Sanika Gavankar", "Head, Partnerships, Public Policy & Customer Success @ Signzy",
     "Signzy", "hiring_manager", 2, "Head, Partnerships & CS",
     "Head of Partnerships, Public Policy & CS at Signzy; AI-led digital banking, identity & compliance."),
    ("priyabrata-priyam", "Priyabrata Pradhan", "VP of Engineering @ Signzy",
     "Signzy", "hiring_manager", 2, "VP Engineering",
     "VP of Engineering at Signzy; AI/GenAI, API platforms, BFSI compliance; 16+ yrs."),
    # Eightfold AI (Product Manager II - Talent Management)
    ("scott-parent-58ba627", "Scott Parent", "VP, Strategic Accounts @ Eightfold AI",
     "Eightfold AI", "leader", 2, "VP, Strategic Accounts",
     "VP Strategic Accounts at Eightfold AI; agentic AI talent intelligence; ex-UKG/Bullhorn."),
    # OfBusiness (Ofb Tech - Product Manager FinTech/NBFC)
    ("ranjankmohapatra", "Dr. Ranjan Kumar Mohapatra", "Independent Director @ OFB Tech",
     "Ofb Tech", "leader", 3, "Independent Director",
     "Independent Director OFB Tech & MapMyIndia; former Director HR Indian Oil; bestselling author."),
    ("vikasyadav", "Vikas Yadav", "Strategy & M&A Leader @ OfBusiness",
     "Ofb Tech", "leader", 2, "Strategy/M&A Leader",
     "Strategy & M&A leader; greenfield CAPEX, acquisitions; 20+ yrs industrial/manufacturing growth."),
    ("arth-patel-78784022", "Arth Patel", "CBO (Fashion Vertical) @ OfBusiness",
     "Ofb Tech", "leader", 2, "CBO, Fashion Vertical",
     "Chief Business Officer, Fashion Vertical at OfBusiness."),
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    # Resolve company_key -> job_id (one job per company among today's spin)
    with get_connection() as conn:
        jobs = conn.execute(
            "SELECT id, company, title FROM jobs WHERE user_id=? AND status='discovered'",
            (USER_ID,),
        ).fetchall()
    company_to_job = {}
    for j in jobs:
        c = (j["company"] or "").lower()
        if "noise" == c.strip().lower():
            company_to_job.setdefault("Noise", (j["id"], j["title"]))
        elif "signzy" == c.strip().lower():
            company_to_job.setdefault("Signzy", (j["id"], j["title"]))
        elif "eightfold" in c:
            company_to_job.setdefault("Eightfold AI", (j["id"], j["title"]))
        elif "ofb tech" in c or "ofbusiness" in c:
            company_to_job.setdefault("Ofb Tech", (j["id"], j["title"]))
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
            url = f"https://www.linkedin.com/in/{slug}"
            if conn.execute(
                "SELECT id FROM contacts WHERE user_id=? AND job_id=? AND linkedin_url LIKE ?",
                (USER_ID, job_id, f"%{slug}%"),
            ).fetchone():
                dup += 1
                continue
            msgs = og.generate(name, ctype, job_title, company_key)
            # Enforce <=200 on connect_note (generator targets it but verify)
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
    print(f"\nDecision-makers inserted: {ins}  Deduped: {dup}")


if __name__ == "__main__":
    main()
