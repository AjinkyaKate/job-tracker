import json
import os
import sys
from datetime import datetime

JOBS_FILE = "jobs.json"


def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return []
    with open(JOBS_FILE) as f:
        return json.load(f)


def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f, indent=2)


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


if __name__ == "__main__":
    main()
