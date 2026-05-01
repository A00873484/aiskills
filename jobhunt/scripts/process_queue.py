"""
Job application queue processor.

Reads job descriptions from queue/*.txt, calls Claude via the `claude` CLI to generate
tailored resume content and outreach messages, then writes outputs to results/<job-slug>/.

Usage:
    python process_queue.py

Requirements:
    Claude Code CLI installed and authenticated (no separate API key needed)

Output per job (in results/<job-slug>/):
    job_description.txt   — copy of the input file
    resume_text.txt       — tailored resume body (plain text, includes <<<ROLE#>>> markers)
    bullet_prefixes.json  — first few words of each bullet, used by run_resume.py for formatting
    job_config.json       — job metadata (slug, company, HM, pdf name)
    outreach.md           — outreach message with subject line
"""

import os
import json
import re
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_DIR = os.path.join(BASE_DIR, "queue")
RESULTS_DIR = os.path.join(BASE_DIR, "results")
PROFILE_PATH = os.path.join(BASE_DIR, "profile.md")


def load_profile() -> str:
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return f.read()


def call_claude(job_description: str, profile: str) -> dict:
    prompt = f"""You are a resume tailoring assistant for a software engineer named Daniel Engelhard.

## Candidate Background
{profile}

## Job Description
{job_description}

Generate tailored resume content and an outreach message for this role.
Return a single JSON object with EXACTLY these fields:

{{
  "job_slug": "company-role-keyword",
  "company": "Company Name",
  "hiring_manager": "Full Name (or 'Hiring Manager' if not found)",
  "output_pdf_name": "resume.pdf",
  "resume_text": "<see format below>",
  "bullet_prefixes": ["First few words of bullet 1", "First few words of bullet 2", ...],
  "outreach_subject": "Subject line for the outreach email",
  "outreach_body": "Full email body (plain text, no markdown)"
}}

### resume_text format rules:
- Plain text, use \\n for newlines
- Start with a 2-3 sentence summary paragraph tailored to this specific role
- Then section headers on their own lines: SKILLS, EXPERIENCE, SIDE PROJECTS, EDUCATION
- Under SKILLS: exactly 3 compact lines of comma-separated skills — NO category labels, just the skills themselves (e.g. "TypeScript, React, Angular, HTML/CSS, SASS, Tailwind CSS")
- Under EXPERIENCE: place EXACTLY these markers on their own lines to indicate role headers:
    <<<ROLE0>>>   (Microsoft, Dec 2021 – 2025)
    <<<ROLE1>>>   (Two Hat, Mar 2021 – Dec 2021)
    <<<ROLE2>>>   (Digital Impact Media, Aug 2015 – Dec 2020)
  Each marker is followed by bullet lines for that role — write each bullet as plain text with NO leading "- " or "*" prefix (the formatter adds bullets visually)
- Under SIDE PROJECTS: one line per project (LLM-RAG Pipeline, Payment App, Inventory Automation)
- End with EDUCATION section

### bullet_prefixes rules:
- Include the first 3-6 words of EVERY bullet line under EXPERIENCE and SIDE PROJECTS
- Do NOT include skill lines — skills are plain text blobs, not bullets
- Example: ["Led end-to-end expansion", "Served as on-call DRI", "LLM-RAG Pipeline:"]

### outreach rules:
- Be direct and concise (under 200 words)
- Acknowledge any honest skill gap (do not oversell)
- For internal Microsoft transfers, lean on that advantage
- No markdown in outreach_body — plain text only

Return ONLY valid JSON. No markdown code fences. No extra commentary."""

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "claude CLI returned non-zero exit code")

    raw = result.stdout.strip()

    # Strip markdown code fences if Claude added them anyway
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    return json.loads(raw)


def write_results(data: dict, job_file: str) -> str:
    job_slug = data["job_slug"]
    out_dir = os.path.join(RESULTS_DIR, job_slug)
    os.makedirs(out_dir, exist_ok=True)

    # Original job description
    with open(job_file, encoding="utf-8") as f:
        job_desc = f.read()
    with open(os.path.join(out_dir, "job_description.txt"), "w", encoding="utf-8") as f:
        f.write(job_desc)

    # Resume body text
    with open(os.path.join(out_dir, "resume_text.txt"), "w", encoding="utf-8") as f:
        f.write(data["resume_text"])

    # Bullet prefixes for formatting detection
    with open(os.path.join(out_dir, "bullet_prefixes.json"), "w", encoding="utf-8") as f:
        json.dump(data["bullet_prefixes"], f, indent=2, ensure_ascii=False)

    # Job metadata
    job_config = {
        "job_slug": data["job_slug"],
        "company": data["company"],
        "hiring_manager": data["hiring_manager"],
        "output_pdf_name": data["output_pdf_name"],
    }
    with open(os.path.join(out_dir, "job_config.json"), "w", encoding="utf-8") as f:
        json.dump(job_config, f, indent=2, ensure_ascii=False)

    # Outreach message
    outreach = f"Subject: {data['outreach_subject']}\n\n{data['outreach_body']}\n"
    with open(os.path.join(out_dir, "outreach.md"), "w", encoding="utf-8") as f:
        f.write(outreach)

    return out_dir


def main():
    if not os.path.exists(QUEUE_DIR):
        print("queue/ directory not found. Create it and add job description .txt files.")
        return

    os.makedirs(RESULTS_DIR, exist_ok=True)

    queue_files = sorted(
        os.path.join(QUEUE_DIR, f)
        for f in os.listdir(QUEUE_DIR)
        if f.endswith(".txt")
    )

    if not queue_files:
        print("No .txt files found in queue/")
        return

    profile = load_profile()
    for job_file in queue_files:
        filename = os.path.basename(job_file)
        print(f"Processing: {filename} ...")
        try:
            data = call_claude(open(job_file, encoding="utf-8").read(), profile)
            out_dir = write_results(data, job_file)
            slug = data["job_slug"]
            hm = data["hiring_manager"]
            print(f"  -> results/{slug}/")
            print(f"     Company:         {data['company']}")
            print(f"     Hiring manager:  {hm}")
            print(f"     PDF name:        {data['output_pdf_name']}")

            # Move processed file out of queue
            done_path = os.path.join(out_dir, "queue_source.txt")
            os.rename(job_file, done_path)
            print(f"     Moved to:        results/{slug}/queue_source.txt")
        except json.JSONDecodeError as e:
            print(f"  ERROR: Claude returned invalid JSON — {e}")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\nDone.")
    print("To generate a PDF, run:")
    print("  python run_resume.py <google_oauth_token> <job_slug>")


if __name__ == "__main__":
    main()
