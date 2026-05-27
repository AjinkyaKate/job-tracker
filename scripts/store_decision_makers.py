"""Store the scraped decision-makers as ranked contacts on their company's job,
with a personalized invite note (<=200) + post-accept follow-up each.

Source: harvestapi/linkedin-company-employees run NEslzDVPHbPuvI4Bu (24 senior
people across 8 AI/SaaS companies). Attribution by company-query sequence.

priority: 1 = HR/recruiter (reach first), 2 = functional hiring-manager/leader,
3 = founder/CEO. contact_type: recruiter / hiring_manager / leader / founder.

Idempotent: dedups by (job_id, linkedin_url).
"""
import sys
from datetime import datetime, timezone
sys.path.insert(0, "/Users/ajinkya/Desktop/Ajinkya Kate/job-tracker")
from db import get_connection  # noqa: E402

USER_ID = 1

# (slug, name, role_label, job_id, contact_type, priority, seniority, about, note, followup)
PEOPLE = [
    # ── Leucine (264) ───────────────────────────────────────────────────────
    ("feroz-siddiqui-653b8628", "Feroz Siddiqui", "Engineering Director @ Leucine", 264, "leader", 2, "Director",
     "Engineering Director, 11+ yrs across AI SaaS, edtech and telecom; led full-stack product builds.",
     "Hi Feroz, saw Leucine is hiring an Associate PM. I'm a Product Owner in martech SaaS, 2+ yrs working close to engineering, and I build with AI hands-on. Would love to connect and learn more about the team.",
     "Thanks for connecting, Feroz. I'm interested in the Associate PM role at Leucine. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) working shoulder to shoulder with engineering on releases and integrations, and I build with the Claude API on the side. I'd love to be considered for the team, happy to share my resume here or apply however you prefer."),
    ("vivek-gera", "Vivek Gera", "CEO @ Leucine", 264, "founder", 3, "Founder/CEO",
     "CEO of Leucine, an AI platform keeping pharma manufacturers compliant and audit-ready.",
     "Hi Vivek, really like what Leucine is doing for compliant pharma manufacturing. I'm a Product Owner in martech SaaS, 2+ yrs, and I build with AI hands-on. Saw the APM opening, would love to connect.",
     "Thanks for connecting, Vivek. What Leucine is building, AI keeping pharma audit-ready across complex workflows, is exactly the kind of regulated, high-stakes product work I find interesting. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing and hands-on with AI. I saw the Associate PM opening and would love to be considered. Happy to share my resume."),
    ("sumanth-chinta-b0935a20", "Sumanth Chinta", "Business Head @ Leucine", 264, "hiring_manager", 2, "Business Head",
     "Business Head at Leucine; 17 yrs digitally transforming regulated industries via integrated quality.",
     "Hi Sumanth, saw Leucine is hiring an Associate PM. I'm a Product Owner in martech SaaS, 2+ yrs, customer-facing and hands-on with AI. Your digital-transformation focus resonates. Would love to connect.",
     "Thanks for connecting, Sumanth. I'm interested in the Associate PM role at Leucine. Your focus on digitally transforming regulated industries through integrated quality is the kind of problem I enjoy. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) doing customer discovery and feature delivery, and I build with AI hands-on. Happy to share my resume and would love to learn more."),
    # ── Credgenics (343) ──────────────────────────────────────────────────────
    ("amit-m-thukral-95709618", "Amit M Thukral", "Global Operations Leader @ Credgenics", 343, "leader", 2, "Ops Leader",
     "Global operations leader, 20+ yrs in collections/lending and customer service, tech-driven CX.",
     "Hi Amit, saw Credgenics is hiring an Associate PM (AI Products). I'm a Product Owner in martech, 2+ yrs, customer-facing and hands-on with AI. Would love to connect and learn more about the team.",
     "Thanks for connecting, Amit. I'm interested in the Associate PM (AI Products) role at Credgenics. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) working close to operations and customers, and I build with AI hands-on (my own job-tracker and a QA agent on the Claude API). Happy to share my resume, would love to hear more."),
    ("goelrishabh", "Rishabh Goel", "Co-founder & CEO @ Credgenics", 343, "founder", 3, "Founder/CEO",
     "Co-founder & CEO, Credgenics; Forbes 30u30, IIT Delhi; AI-powered debt collections for BFSI.",
     "Hi Rishabh, really admire what Credgenics is building in AI-led collections. I'm a Product Owner in martech, 2+ yrs, and I build with AI hands-on. Saw the APM (AI Products) opening, would love to connect.",
     "Thanks for connecting, Rishabh. Credgenics reimagining collections for the BFSI with AI is a great problem space, and the Associate PM (AI Products) role looks like a strong fit for how I work. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing, and I build with the Claude API hands-on. I'd love to be considered, happy to share my resume."),
    ("vishal-mishra-57592325", "Vishal Mishra", "Associate Director, Engineering @ Credgenics", 343, "leader", 2, "Assoc Director, Eng",
     "Associate Director of Engineering at Credgenics; ex-EM at Pine Labs.",
     "Hi Vishal, saw Credgenics is hiring an Associate PM (AI Products). I'm a Product Owner in martech who works close to engineering and builds with AI hands-on. Would love to connect and learn more.",
     "Thanks for connecting, Vishal. I'm interested in the Associate PM (AI Products) role at Credgenics. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) partnering closely with engineering on releases, and I build with the Claude API myself, so I can speak your team's language. Happy to share my resume and hear more about the role."),
    # ── Zoca (260) ────────────────────────────────────────────────────────────
    ("chintangandhi8", "Chintan Gandhi", "AI Products @ Zoca (Ex-Unacademy)", 260, "hiring_manager", 2, "Product Lead",
     "Leads AI Products at Zoca; ex-Unacademy; 3+ yrs building products for 10M+ users.",
     "Hi Chintan, saw Zoca is hiring an AI Product Manager on your team. I'm a Product Owner in martech, 2+ yrs, and I ship AI features hands-on with the Claude API. Would love to connect and learn how you build at Zoca.",
     "Thanks for connecting, Chintan. The AI Product Manager role on your team at Zoca really caught my eye. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, and I build with AI hands-on (I shipped a job-tracker and a QA automation agent on the Claude API). Making a full calendar the default for salons is a fun, real problem. I'd love to be considered, happy to share my resume."),
    ("ashish-verma-zoca", "Ashish Verma", "Founder @ Zoca", 260, "founder", 3, "Founder",
     "Building Zoca; making a fully booked calendar the default for salons and spas.",
     "Hi Ashish, love the Zoca mission of making a full calendar the default for salons. I'm a Product Owner in martech who builds with AI hands-on. Saw the AI PM opening, would love to connect.",
     "Thanks for connecting, Ashish. What you're building at Zoca for salons and spas is a sharp, focused product, and the AI Product Manager role fits how I already work. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing, and I ship with the Claude API hands-on. I'd love to be considered, happy to share my resume."),
    ("syedbilal-", "Syed Bilal", "Customer Success Manager @ Zoca", 260, "leader", 2, "CS Manager",
     "Customer success manager, 9 yrs in client relationships, adoption and retention across US/UK/Canada.",
     "Hi Syed, saw Zoca is growing the team. I'm a Product Owner in martech, 2+ yrs, very customer-facing, and I build with AI hands-on. Would love to connect and hear how things are at Zoca.",
     "Thanks for connecting, Syed. I'm exploring roles at Zoca, the AI Product Manager opening especially. As someone close to customer success, you'd know how the product and customer sides work together there, which is exactly where I operate. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs. Would love to hear your take, and happy to share my resume."),
    # ── Neuron7 (263) ─────────────────────────────────────────────────────────
    ("nikenpatel", "Niken Patel", "Founder & CEO @ Neuron7.ai", 263, "founder", 3, "Founder/CEO",
     "Founder & CEO, Neuron7; agentic AI for mission-critical service; 20+ yrs, multiple exits.",
     "Hi Niken, agentic AI for mission-critical service is a great space. I'm a Product Owner in martech who builds with AI/LLMs hands-on. Saw Neuron7 is hiring AI Solutions Engineers, would love to connect.",
     "Thanks for connecting, Niken. Neuron7's agentic AI for service resolution is exactly the kind of applied-AI product I'm drawn to. I'm a Product Owner at D·engage (CPaaS/martech), customer-facing, and I build with LLMs hands-on (my own tools on the Claude API). I saw the AI Solutions Engineer roles and would love to be considered. Happy to share my resume."),
    ("amitverma26", "Amit Verma", "Founding Head of Technology & AI @ Neuron7.ai", 263, "hiring_manager", 2, "Head of Eng/AI",
     "Founding Head of Engineering & AI at Neuron7; ex-Tibco/Trilogy/Oracle; deep AI/data background.",
     "Hi Amit, saw Neuron7 is hiring AI Solutions Engineers. I'm a customer-facing Product Owner who builds with LLMs and agent frameworks hands-on. The role looks right up my alley, would love to connect.",
     "Thanks for connecting, Amit. The AI Solutions Engineer role at Neuron7 fits how I work, customer-facing plus hands-on AI. I'm a Product Owner at D·engage (CPaaS/martech) and I've built my own tools with the Claude API (a job-tracker and a QA automation agent), so I'm comfortable in Python and LLM/agent workflows. I'd love to be considered, happy to share my resume and talk through the role."),
    ("marc-silberstrom-252176", "Marc Silberstrom", "Chief Sales Officer @ Neuron7.ai", 263, "leader", 2, "CSO",
     "Chief Sales Officer at Neuron7; 20+ yrs scaling GTM at AI/SaaS/enterprise software companies.",
     "Hi Marc, saw Neuron7 is hiring AI Solutions Engineers. I'm a customer-facing Product Owner in martech who builds with AI hands-on; the pre-sales/solutions side is where I do best. Would love to connect.",
     "Thanks for connecting, Marc. The AI Solutions Engineer role at Neuron7 caught my eye, the mix of customer-facing work and explaining AI solutions is exactly what I enjoy. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs doing demos, scoping and onboarding, and I build with LLMs hands-on. I'd love to be considered for your team, happy to share my resume."),
    # ── Tech Prescient (258) ──────────────────────────────────────────────────
    ("amitarole", "Amit Arole", "Founder & CEO @ Tech Prescient", 258, "founder", 3, "Founder/CEO",
     "Founder & CEO, Tech Prescient; building Identity Confluence, an AI-driven IGA/identity-security platform.",
     "Hi Amit, Identity Confluence and the AI-driven IGA space is really interesting. I'm a Product Owner in martech who builds with AI hands-on, and I'm in Pune too. Saw the PM (IAM/IGA) opening, would love to connect.",
     "Thanks for connecting, Amit. What Tech Prescient is building with Identity Confluence, continuous AI-assisted identity governance, is a strong, timely product, and the PM (IAM/IGA) role is a great fit for me. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing and hands-on with AI, and I'm based in Pune. I'd love to be considered, happy to share my resume."),
    ("kishor-v-kulkarni", "Kishor Kulkarni", "Chief Growth Officer @ Tech Prescient", 258, "leader", 2, "CGO",
     "Chief Growth Officer at Tech Prescient; 26 yrs in IT/cybersecurity leadership, presales and GTM.",
     "Hi Kishor, saw Tech Prescient is hiring a PM for IAM/IGA. I'm a Product Owner in martech SaaS, 2+ yrs, customer-facing and hands-on with AI, based in Pune. Would love to connect and learn more.",
     "Thanks for connecting, Kishor. I'm interested in the PM (IAM/IGA) role at Tech Prescient. Identity governance is a sharp space and the role fits my background; I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) doing PRDs, roadmaps and customer-facing work, and I'm Pune-based. Happy to share my resume and would love to hear more."),
    ("sudhirgokhale", "Sudhir Gokhale", "Head of Product @ Tech Prescient", 258, "hiring_manager", 2, "Head of Product",
     "Head of Product at Tech Prescient (Identity Confluence); 23+ yrs in enterprise software product engineering.",
     "Hi Sudhir, saw you're building Identity Confluence and hiring a PM for IAM/IGA. I'm a Product Owner in martech SaaS, 2+ yrs, hands-on with AI, based in Pune. Would love to connect and learn more about the role.",
     "Thanks for connecting, Sudhir. The PM (IAM/IGA) role on your team at Tech Prescient really fits me. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) owning PRDs, user stories and roadmaps with engineering, and I build with AI hands-on. I'm Pune-based, so on-site works well too. I'd love to be considered, happy to share my resume and walk through my work."),
    # ── Kambaa (356) ──────────────────────────────────────────────────────────
    ("sukinshetty-1984", "Sukin Shetty", "Enterprise AI Architect @ Kambaa", 356, "leader", 2, "AI Architect",
     "Enterprise AI Architect; agentic AI systems, pre-sales solution mapping and stakeholder discovery.",
     "Hi Sukin, your work on agentic AI and pre-sales solution mapping is exactly the kind of role I'm targeting. I'm a Product Owner in martech who builds with the Claude API hands-on. Would love to connect.",
     "Thanks for connecting, Sukin. The way you describe your work, agentic AI, pre-sales discovery, solution mapping, is exactly the Solutions Engineer space I'm moving toward. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs customer-facing, and I build AI agents and tools hands-on with the Claude API. Kambaa has a Presales/Solutions Engineer opening I'd love to be considered for. Happy to share my resume, and would value your perspective on the role."),
    ("jaganivas", "Jagan S.", "Co-Founder @ Kambaa", 356, "founder", 3, "Co-Founder",
     "Co-founder; 20+ yrs in sales/consulting (EY, PwC, IBM, Wipro); building D2C SaaS and an AI Agent Factory.",
     "Hi Jagan, I like the breadth of what you're building, especially the AI agent and SaaS work. I'm a Product Owner in martech who ships with AI hands-on. Saw Kambaa's Solutions Engineer opening, would love to connect.",
     "Thanks for connecting, Jagan. Your range across D2C SaaS and an AI Agent Factory is the kind of building I enjoy. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs customer-facing, and I build with the Claude API hands-on. Kambaa's Presales/Solutions Engineer role looks like a strong fit, I'd love to be considered. Happy to share my resume."),
    # ── peopleHum (257) ───────────────────────────────────────────────────────
    ("aishwarya-jain-business-leader", "Aishwarya Jain", "Director Sales @ peopleHum", 257, "leader", 2, "Director, Sales",
     "Director Sales at peopleHum; B2B SaaS enterprise sales, partnerships and global markets (HR tech).",
     "Hi Aishwarya, saw peopleHum is hiring an Associate PM. I'm a Product Owner in B2B SaaS, 2+ yrs, customer-facing and hands-on with AI. Would love to connect and learn more about the team.",
     "Thanks for connecting, Aishwarya. I'm interested in the Associate PM role at peopleHum. I've spent 2+ years as a Product Owner at D·engage (a B2B CPaaS/martech SaaS) working close to customers and sales, and I build with AI hands-on. Happy to share my resume, would love to hear more about the team and the role."),
    ("varmapankaj69", "Pankaj Varma", "Director HR @ peopleHum", 257, "recruiter", 1, "Director, HR",
     "Director HR at peopleHum; people and project leadership, workplace innovation.",
     "Hi Pankaj, saw peopleHum is hiring an Associate PM. I'm a Product Owner in B2B SaaS, 2+ yrs, customer-facing and hands-on with AI. Would love to connect and be considered for the role.",
     "Thanks for connecting, Pankaj. I'd love to be considered for the Associate PM role at peopleHum. I've spent 2+ years as a Product Owner at D·engage (a B2B CPaaS/martech SaaS), customer-facing and quality-focused, and I build with AI hands-on. I'm sharing my resume here, and happy to apply through whatever process you prefer. Thanks for considering."),
    ("dnachnani", "Deepak Nachnani", "Co-founder, Avniro (peopleHum)", 257, "founder", 3, "Co-Founder",
     "Co-founder of Avniro group (peopleHum's parent); building SaaS brands on real B2B/B2C gaps with AI.",
     "Hi Deepak, I admire the Avniro vision of a SaaS conglomerate built on real customer gaps with AI. I'm a Product Owner in B2B SaaS who builds with AI hands-on. Saw peopleHum's APM opening, would love to connect.",
     "Thanks for connecting, Deepak. The Avniro approach, building SaaS brands around real B2B/B2C gaps with AI and automation, is the kind of product thinking I'm drawn to. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing and hands-on with AI. I saw the Associate PM opening at peopleHum and would love to be considered. Happy to share my resume."),
    # ── CoreTek (353) ─────────────────────────────────────────────────────────
    ("srikanth-sk-8a5ba5b2", "Srikanth SK", "Leadership @ CoreTek Labs", 353, "leader", 2, "Leadership",
     "13 yrs in consulting and executive leadership; large-scale enterprise systems, product and services.",
     "Hi Srikanth, saw CoreTek is hiring a Product Manager. I'm a Product Owner in martech, 2+ yrs, customer-facing and hands-on with AI/ML products. Would love to connect and learn more about the team.",
     "Thanks for connecting, Srikanth. I'm interested in the Product Manager role at CoreTek. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech) working across product and engineering, and I build with AI hands-on. Happy to share my resume, would love to hear more about the role and team."),
    ("pradeepkanneganti", "Pradeep Kanneganti", "Founder & CEO @ CoreTek Labs", 353, "founder", 3, "Founder/CEO",
     "Founder & CEO, CoreTek Labs; enterprise solutions through innovative cloud and AI.",
     "Hi Pradeep, like CoreTek's focus on solving business problems with cloud and AI. I'm a Product Owner in martech who builds with AI hands-on. Saw the PM opening, would love to connect.",
     "Thanks for connecting, Pradeep. CoreTek's focus on delivering enterprise solutions through cloud and AI is a space I enjoy. I'm a Product Owner at D·engage (CPaaS/martech), 2+ yrs, customer-facing and hands-on with AI. I saw the Product Manager opening and would love to be considered. Happy to share my resume."),
    ("priya-rao-4b6155123", "Priya Rao", "Business Manager / HR @ CoreTek Labs", 353, "recruiter", 1, "HR / Business Mgr",
     "Business Manager at CoreTek; 10+ yrs in HR and recruitment across IT and non-IT.",
     "Hi Priya, saw CoreTek is hiring a Product Manager. I'm a Product Owner in martech, 2+ yrs, customer-facing and hands-on with AI/ML products. Would love to connect and be considered for the role.",
     "Thanks for connecting, Priya. I'd love to be considered for the Product Manager role at CoreTek. I've spent 2+ years as a Product Owner at D·engage (CPaaS/martech), customer-facing and close to engineering, and I build with AI hands-on. Sharing my resume here, and happy to go through whatever process works. Thanks for considering."),
]


def main():
    now = datetime.now(timezone.utc).isoformat()
    inserted = dup = 0
    over = []
    with get_connection() as conn:
        for (slug, name, role, job_id, ctype, prio, sen, about, note, follow) in PEOPLE:
            url = f"https://www.linkedin.com/in/{slug}"
            if len(note) > 200:
                over.append((name, len(note)))
            if conn.execute(
                "SELECT id FROM contacts WHERE user_id=? AND job_id=? AND linkedin_url LIKE ?",
                (USER_ID, job_id, f"%{slug}%")).fetchone():
                dup += 1
                continue
            conn.execute(
                "INSERT INTO contacts (user_id, job_id, name, role, linkedin_url, "
                "connect_note, followup_msg, contact_type, priority, seniority, "
                "about, added_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                (USER_ID, job_id, name, role, url, note, follow, ctype, prio,
                 sen, about, now))
            inserted += 1
        conn.commit()
    print(f"Decision-makers inserted: {inserted}  Deduped: {dup}")
    if over:
        print("WARNING notes over 200:", over)
    else:
        print(f"All {len(PEOPLE)} invite notes within 200 chars.")
    print("Note lengths:", sorted(len(p[8]) for p in PEOPLE))


if __name__ == "__main__":
    main()
