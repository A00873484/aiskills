---
name: make-resume
description: Use this skill when the user wants to generate, update, or rebuild their resume in Google Docs. Triggers on phrases like "make my resume", "update my resume", "generate my resume", "rebuild the resume", "write my resume", "push my resume to Google Docs", or "update the active resume".
version: 3.0.0
---

# Make Resume Skill

Generate a tailored one-page resume from a job description, write it into the active Google Doc with full formatting, and export a PDF to the local resumes folder.

## Pipeline Overview

```
queue/<filename>.txt  →  process_queue.py  →  results/<job-slug>/  →  run_resume.py  →  PDF
```

All scripts live in `jobhunt/`. Config is read from `jobhunt/config.json`. The candidate background profile is at `jobhunt/profile.md`.

---

## Step 1 — Get the job description

If the user hasn't pasted a job description, ask for it. Save it to `jobhunt/queue/<descriptive-filename>.txt` — e.g. `microsoft_hpc_ai.txt`.

---

## Step 2 — Process the queue

```bash
cd jobhunt
python process_queue.py
```

This calls the Claude API (`ANTHROPIC_API_KEY` must be set) to tailor the resume content and generate an outreach message. Outputs land in `results/<job-slug>/`:

| File | Contents |
|------|----------|
| `resume_text.txt` | Tailored resume body with `<<<ROLE#>>>` markers |
| `bullet_prefixes.json` | First few words of each bullet (used for formatting) |
| `job_config.json` | Metadata: company, hiring manager, PDF name |
| `outreach.md` | Outreach email with subject line |
| `job_description.txt` | Copy of the input |

If `ANTHROPIC_API_KEY` is not set, ask the user to set it:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

---

## Step 3 — Generate the PDF

Get a Google OAuth token, then run the generic resume runner:

```bash
TOKEN=$(gcloud auth print-access-token)
python run_resume.py "$TOKEN" <job-slug>
```

The job slug is printed by `process_queue.py` and matches the folder name under `results/`.

If auth fails, ask the user to run:
```bash
gcloud auth login --enable-gdrive-access
```

---

## Step 4 — Show the outreach message

After the PDF is generated, read and display `results/<job-slug>/outreach.md` so the user can copy it directly.

---

## How it works (for reference)

`run_resume.py` is the generic Google Docs runner. It:
1. Loads personal details from `config.json`
2. Loads `resume_text.txt`, `bullet_prefixes.json`, and `job_config.json` from the results folder
3. Replaces the Google Doc content and applies formatting (role header tables, bullets, font sizes)
4. Exports a PDF to `config.json → resumes_dir`

`process_queue.py` is the Claude-powered tailoring step. It reads `profile.md` and the job description, then generates the resume body and outreach message as plain text files. Do NOT write new Python scripts — use these two scripts for everything.

---

## One-Page Length Target

The resume must fit on exactly one page. If the user reports it's running long, edit `results/<job-slug>/resume_text.txt` directly and re-run `run_resume.py`. Trim in this order:
1. Cut the least impactful bullet per role (max 7 bullets for Microsoft, 3 for Two Hat, 3 for Digital Impact Media)
2. Keep Side Projects to 3 entries, 1 line each
3. Do not shrink font below 10pt or margins below 36pt
