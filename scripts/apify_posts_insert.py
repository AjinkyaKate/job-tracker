"""Insert the genuinely-relevant LinkedIn hiring POSTS (source=linkedin-post).

Source: harvestapi/linkedin-post-search run EbStGNxDvFpbW3Njg.
24 posts scraped; the vast majority were listicle/roundup/job-seeker noise.
Only the 3 below are real, in-lane, DM-able hiring posts for Ajinkya, so only
these get added. The post author becomes the contact (person to reach out to).

Idempotent: dedups by link.
"""
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402

USER_ID = 1


def s(v):
    if v is None:
        return ""
    if isinstance(v, (list, tuple)):
        return ", ".join(str(x) for x in v if x not in (None, ""))
    return str(v)


def clean_url(u):
    return (u or "").split("?")[0]


POSTS = [
    {"title": "Customer Success Mgr / Onboarding & Implementation Mgr / Support Engineer",
     "org": "BIK", "city": "Bangalore",
     "url": "https://www.linkedin.com/posts/swadhasharma_hiring-customersuccess-activity-7465280826797219840-YcGM",
     "work": "On-site", "level": "Associate", "yoe": "2-5 yrs",
     "content": "Expanding the Customer Experience team at BIK, hiring across customer-facing roles in Bangalore. Open roles: Customer Success Manager (India) 2-5y; Onboarding & Implementation Manager 2-5y; Support Engineer 2-5y. Wants excellent communication, strong client-facing experience, ownership + problem-solving, SaaS customer experience a must. In-office Bangalore (5 days/week). DM the poster to apply.",
     "skills": ["Customer Success", "Onboarding", "Implementation", "SaaS", "Client-facing", "Problem Solving"],
     "score": "STRONG",
     "reason": "Direct hiring-manager post, customer-facing SaaS, 2-5yr band, DM-able. Strong CSE/CSM lane match.",
     "rname": "Swadha Sharma", "rtitle": "All things Customer Success @ BIK (hiring manager)",
     "rurl": "https://www.linkedin.com/in/swadhasharma", "remail": ""},

    {"title": "Solutions Engineer (Pre-Sales) / Technical Account Mgr / Enterprise CS",
     "org": "TalentXO (multiple clients)", "city": "Remote / Noida / Bengaluru",
     "url": "https://www.linkedin.com/posts/mohitgoyal2151_hiring-jobs-nowhiring-activity-7464638009540448256-CTYg",
     "work": "Remote", "level": "Associate", "yoe": "1-15 yrs",
     "content": "Recruiter roundup across product/SaaS/fintech/AI/adtech brands. Relevant to you: Solutions Engineer (Pre-Sales, B2B Tech) Remote; Technical Account Manager (Customer Success, Adtech) Noida; Enterprise Customer Success (CPaaS, Telecom) Bengaluru. Email CV to mohit.goyal@talentxo.in with the role name in the subject line.",
     "skills": ["Solutions Engineering", "Pre-Sales", "Technical Account Management", "Customer Success", "B2B SaaS"],
     "score": "MAYBE",
     "reason": "Agency recruiter with 3 relevant customer-facing/SE roles + a direct email. Reachable, but not a single named role.",
     "rname": "Mohit Goyal", "rtitle": "Talent Partner @ TalentXO (recruiter)",
     "rurl": "https://www.linkedin.com/in/mohitgoyal2151", "remail": "mohit.goyal@talentxo.in"},

    {"title": "Senior Technical Product Manager (works alongside AI agents)",
     "org": "partao", "city": "Remote / Hybrid (India)",
     "url": "https://www.linkedin.com/posts/kate-reeves-certrp-698636168_productmanagement-technicalpm-remotework-activity-7465343943782813696-6fwx",
     "work": "Hybrid", "level": "Mid-Senior level", "yoe": "5+ yrs",
     "content": "partao is hiring a Senior Technical PM to work shoulder-to-shoulder with AI agents: explore the codebase, draft requirements, propose architectures, turn ideas into engineering-ready tickets. Wants 5+ yrs PM (at least 2 in a technical role), strong technical fluency, e-commerce/marketplace/high-volume consumer product experience, hands-on AI tooling. Apply via link in comments or reach out to the poster directly.",
     "skills": ["Technical PM", "AI Tooling", "Marketplace", "E-commerce", "Requirements", "Architecture"],
     "score": "MAYBE",
     "reason": "AI-agent-driven PM role fits your builder story; direct contact. Stretch: wants 5+ yrs (you have ~2).",
     "rname": "Kate Reeves", "rtitle": "Talent Partner @ partao (recruiter)",
     "rurl": "https://www.linkedin.com/in/kate-reeves-certrp-698636168", "remail": ""},
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = 0
    with get_connection() as conn:
        for p in POSTS:
            link = clean_url(p["url"])
            if conn.execute("SELECT id FROM jobs WHERE user_id = ? AND link = ?",
                            (USER_ID, link)).fetchone():
                dup += 1
                continue
            cur = conn.execute(
                "INSERT INTO jobs (user_id, title, company, link, location, "
                "work_arrangement, level, yoe_required, posted_at, source, "
                "jd_summary, must_have_skills, jd_raw_text, ai_score, "
                "ai_score_reason, status, added_at) VALUES "
                "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, s(p["title"]), s(p["org"]), link, s(p["city"]),
                 s(p["work"]), s(p["level"]), s(p["yoe"]), now, "linkedin-post",
                 s(p["content"]), s(p["skills"]), s(p["content"]), p["score"],
                 s(p["reason"]), "discovered", now),
            )
            job_id = cur.lastrowid
            conn.execute(
                "INSERT INTO contacts (user_id, job_id, name, role, linkedin_url, "
                "email, added_at) VALUES (?,?,?,?,?,?,?)",
                (USER_ID, job_id, s(p["rname"]), s(p["rtitle"]),
                 clean_url(p["rurl"]), s(p["remail"]), now),
            )
            inserted += 1
        conn.commit()
    print(f"Posts inserted: {inserted}  Deduped: {dup}")
    with get_connection() as conn:
        total = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? AND status = 'discovered'",
            (USER_ID,)).fetchone()["n"]
        posts = conn.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE user_id = ? AND source = 'linkedin-post'",
            (USER_ID,)).fetchone()["n"]
    print(f"Total discovered: {total}  (from posts: {posts})")


if __name__ == "__main__":
    main()
