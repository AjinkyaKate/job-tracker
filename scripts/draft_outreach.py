"""Draft + store the LinkedIn invite note (<=200) and the post-accept follow-up
for each discover contact, in Ajinkya's voice (plain, human, NO em-dashes).

Keyed by the public identifier in the contact's linkedin_url so a person who
appears on several jobs (e.g. one recruiter on 3 listings) gets the same note.
Enriched profiles (Swadha/Roehan/Bhola) get deeper, specific notes.

Idempotent: overwrites connect_note/followup_msg on matching discovered contacts.
"""
import sys
sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402

USER_ID = 1

# slug -> (connect_note <=200, followup_msg)
MESSAGES = {
    # ── Enriched (deep personalization) ─────────────────────────────────────
    "swadhasharma": (
        "Hi Swadha, saw BIK is hiring across Customer Success and Onboarding in Bangalore. I'm a Product Owner in CPaaS/martech, 2+ yrs working closely with customers on adoption. Would love to connect.",
        "Thanks for connecting, Swadha. I saw BIK is hiring across Customer Success and Onboarding. I've spent 2+ years as a Product Owner at D·engage (a CPaaS/martech platform) working hands-on with customers on onboarding, adoption and feature rollout, so the customer-facing side is exactly where I do my best work. Given your background scaling CS at CleverTap and LinkedIn, I'd genuinely value the chance to do that at BIK. Happy to share my resume here or apply wherever you prefer.",
    ),
    "iamroehan": (
        "Hi Roehan, saw your Presales/Solutions Engineer role at Kambaa. I'm a Product Owner in martech, customer-facing and hands-on building with AI. The growth-through-tech angle resonates. Keen to connect.",
        "Thanks for connecting, Roehan. Your Presales/Solutions Engineer opening at Kambaa caught my eye, the mix of customer-facing work and explaining technical solutions is what I enjoy most. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) doing demos, integration scoping and onboarding, and I build with AI on the side (I shipped a job-tracker and a QA automation tool myself). Your goSTOPS product-and-growth story is the kind of building I'm drawn to. Happy to share my resume, would love to hear more.",
    ),
    "bhola-meena": (
        "Hi Bhola, saw Kaabil is hiring an Associate PM. I'm a Product Owner in martech, 2+ yrs, and I build with AI hands-on (shipped my own tools). Your AI-for-efficiency focus resonates. Keen to connect.",
        "Thanks for connecting, Bhola. I saw the Associate PM role at Kaabil. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech), and like your recent focus, I lean heavily on AI to move faster, I've built a job-tracker and a QA automation tool end to end with the Claude API. Coming from your Microsoft and IIT-K background, I'd love to learn how you're applying AI at Kaabil and bring that hands-on, AI-first product approach to the team. Happy to share my resume.",
    ),
    # ── Founder / tech-leader poster ────────────────────────────────────────
    "pulkit-tiwari": (
        "Hi Pulkit, saw Arré is hiring a Growth PM. I'm a Product Owner in martech, 2+ yrs, and I build with AI hands-on. Would love to connect and follow what you're building at Arré.",
        "Thanks for connecting, Pulkit. I saw the Growth PM role at Arré. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) and I build with AI on the side (my own job-tracker and a QA automation tool). If the search is still open I'd love to throw my hat in, happy to share my resume. Either way, glad to connect and follow the work at Arré.",
    ),
    # ── Neuron7 (one person, 3 AI Solutions Engineer listings) ──────────────
    "rajeshkrsinghhr": (
        "Hi Rajesh, saw Neuron7 is hiring AI Solutions Engineers. I'm a customer-facing Product Owner in martech who builds with AI and LLMs hands-on. The role looks right up my alley. Keen to connect.",
        "Thanks for connecting, Rajesh. The AI Solutions Engineer roles at Neuron7 caught my eye, the mix of customer-facing work and hands-on AI/LLM building is exactly what I enjoy. I'm a Product Owner at D·engage (CPaaS/martech) and I've built my own tools with the Claude API (a job-tracker and a QA automation agent). Happy to share my resume and would love to hear more about the team.",
    ),
    # ── PM/APM recruiters (role-referenced, honest on stretch) ──────────────
    "ruppal-agarwal": (
        "Hi Ruppal, saw Leucine is hiring an Associate PM. I'm a Product Owner in CPaaS/martech, 2+ yrs, and I build with AI hands-on. Would love to connect and learn more about the role.",
        "Thanks for connecting, Ruppal. I'm interested in the Associate PM role at Leucine. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) working closely with engineering and customers, and I build with AI on the side. I'd love to be considered, happy to share my resume here or apply however you prefer.",
    ),
    "mg43023212b": (
        "Hi Malvika, saw Augnito is hiring a Product Manager. I'm a Product Owner in martech, 2+ yrs, customer-facing and hands-on with AI. Would love to connect and learn more about the role.",
        "Thanks for connecting, Malvika. I came across the Product Manager role at Augnito. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) and build with AI hands-on. I know the role may lean a bit more senior, but I'd love to be considered if there's a fit. Happy to share my resume.",
    ),
    "samyaka-lokhande": (
        "Hi Samyaka, saw Acronotics is hiring AI Solutions Engineers. I'm a customer-facing Product Owner in martech who builds with AI and LLMs. Would love to connect and hear more.",
        "Thanks for connecting, Samyaka. The AI Solutions Engineer opening at Acronotics caught my eye. I'm a Product Owner at D·engage (CPaaS/martech), customer-facing, and I build with the Claude API hands-on (my own job-tracker and a QA agent). Happy to share my resume if you think there's a fit.",
    ),
    "filisha-bhoraniya": (
        "Hi Filisha, saw Innova is hiring a Technical PM in AI/Healthcare. I'm a Product Owner in martech, 2+ yrs, hands-on with AI products. Would love to connect and learn more.",
        "Thanks for connecting, Filisha. I'm interested in the Technical PM role at Innova ESI. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) and I build AI-driven tools hands-on. Happy to share my resume, would love to hear more about the role and team.",
    ),
    "subhashis-dash": (
        "Hi Subhashis, saw Sense is hiring a Product Manager. I'm a Product Owner in CPaaS/martech, 2+ yrs, customer-facing and hands-on with AI. Would love to connect and learn more.",
        "Thanks for connecting, Subhashis. I came across the Product Manager role at Sense. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech), close to both customers and engineering, and I build with AI on the side. Happy to share my resume if there's a fit.",
    ),
    "aditi-s-b016a6163": (
        "Hi Aditi, saw CoinSwitch is hiring a Product Manager. I'm a Product Owner in martech, 2+ yrs, customer-facing and hands-on with AI. Would love to connect and hear more about the role.",
        "Thanks for connecting, Aditi. I'm interested in the Product Manager II role at CoinSwitch. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech), and I build with AI hands-on. Happy to share my resume, would love to learn more about the team.",
    ),
    "sahuarchana": (
        "Hi Archana, saw Zopper is hiring a PM for Bancassurance & SaaS. I'm a Product Owner in CPaaS/martech SaaS, 2+ yrs, API-platform and customer-facing. Would love to connect and learn more.",
        "Thanks for connecting, Archana. I'm interested in the PM (Bancassurance & SaaS) role at Zopper. I've spent 2+ years as a Product Owner at D·engage, a CPaaS/martech SaaS, working on API integrations and customer-facing features. Happy to share my resume here or apply however you prefer.",
    ),
    "ishanrohera": (
        "Hi Ishan, saw DXFactor is hiring a PM (Adtech/Media), remote. I'm a Product Owner in martech, 2+ yrs, customer-facing and hands-on with AI tools. Would love to connect and learn more.",
        "Thanks for connecting, Ishan. The remote PM (Adtech/Media) role at DXFactor caught my eye. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) and I use AI tools heavily in how I work. Happy to share my resume, would love to hear more about the role.",
    ),
    "kawaljeet-singh": (
        "Hi Kawaljeet, saw E2M is hiring a Product Manager. I'm a Product Owner in CPaaS/martech, 2+ yrs, Agile and hands-on with AI/ML products. Would love to connect and learn more.",
        "Thanks for connecting, Kawaljeet. I'm interested in the Product Manager role at E2M. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech), working in Agile with engineering and using AI hands-on. Happy to share my resume or apply however works best.",
    ),
    "mohitgoyal2151": (
        "Hi Mohit, saw your post with the Solutions Engineer and Customer Success roles. I'm a customer-facing Product Owner (2+ yrs, CPaaS/martech). Would love to connect and explore a fit.",
        "Thanks for connecting, Mohit. A few of the roles you posted fit me well, the Solutions Engineer (Pre-Sales) and the Customer Success/TAM roles especially. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing and hands-on with product and AI. I'd love to be put forward for any of those. I'll email my resume to mohit.goyal@talentxo.in with the role in the subject, as your post asked. Thanks!",
    ),
    "kate-reeves": (
        "Hi Kate, your Senior Technical PM role at partao resonates, working alongside AI agents is how I already build. I'm a Product Owner in martech who ships with the Claude API. Keen to connect.",
        "Thanks for connecting, Kate. The partao Senior Technical PM role stood out, working shoulder-to-shoulder with AI agents to turn ideas into tickets is literally how I already work. I'm a Product Owner at D·engage (CPaaS/martech), and I've built my own tools with the Claude API (a job-tracker and a QA automation agent). I know you're after 5+ yrs and I'm at 2+, but the AI-native way of working is second nature to me. Happy to share my resume if you're open to it.",
    ),
}


def main():
    over = []
    updated = 0
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT ct.id, ct.linkedin_url, ct.name FROM contacts ct "
            "JOIN jobs j ON ct.job_id = j.id "
            "WHERE ct.user_id = ? AND j.status = 'discovered'", (USER_ID,)
        ).fetchall()
        for r in rows:
            url = (r["linkedin_url"] or "").lower()
            match = next((slug for slug in MESSAGES if slug in url), None)
            if not match:
                continue
            note, follow = MESSAGES[match]
            if len(note) > 200:
                over.append((r["name"], len(note)))
            conn.execute(
                "UPDATE contacts SET connect_note = ?, followup_msg = ? WHERE id = ?",
                (note, follow, r["id"]),
            )
            updated += 1
        conn.commit()

    print(f"Contacts updated: {updated}")
    print("Char counts (invite note):")
    for slug, (note, _) in MESSAGES.items():
        flag = "  <-- OVER 200" if len(note) > 200 else ""
        print(f"  {len(note):>3}  {slug}{flag}")
    if over:
        print("\nWARNING: notes over 200:", over)
    else:
        print("\nAll invite notes within LinkedIn's 200-char limit.")


if __name__ == "__main__":
    main()
