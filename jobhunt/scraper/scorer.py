"""Score job postings for fit and write high-fit jobs to the queue."""
import json
import os
import re
import subprocess
from pathlib import Path


def _slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    return text[:50].strip("-")


def _call_claude_score(title: str, company: str, content: str, profile: str) -> dict:
    prompt = f"""Rate this job posting for fit with the candidate. Return ONLY a JSON object.

## Candidate Profile
{profile}

## Job: {title} at {company}
{content[:2500]}

Scoring guide:
- 5: Near-perfect (design systems, senior frontend, TypeScript/React, accessibility)
- 4: Strong (senior frontend TypeScript/React, good culture/stack fit)
- 3: Decent (frontend role, relevant skill overlap)
- 2: Weak (junior, wrong stack, or marginal overlap)
- 1: Poor (backend-only, data science, mobile, not frontend)

Return ONLY valid JSON, no code fences:
{{"fit": 1-5, "reason": "one sentence explaining the score", "keep": true/false}}

keep=true when fit >= 3."""

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    raw = result.stdout.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


def score_and_queue(
    jobs: list[dict],
    profile: str,
    blocklist: list[str],
    fit_threshold: int,
    queue_dir: Path,
) -> int:
    """Score each job and write keepers to queue_dir. Returns count of queued jobs."""
    queue_dir.mkdir(exist_ok=True)
    queued = 0

    for job in jobs:
        title = job.get("title", "")
        company = job.get("company", "")
        content = job.get("content", "")
        apply_url = job.get("url", "")

        # Blocklist check (fast, no Claude call needed)
        combined = title.lower()
        blocked_by = next((kw for kw in blocklist if kw.lower() in combined), None)
        if blocked_by:
            print(f"  SKIP [{company}] {title} — blocked: {blocked_by!r}")
            continue

        # Generate slug and check if already in queue or results
        slug = _slugify(f"{company}-{title}")
        queue_file = queue_dir / f"{slug}.txt"
        results_dir = queue_dir.parent / "results" / slug
        if queue_file.exists() or results_dir.exists():
            print(f"  SKIP [{company}] {title} — already queued/processed")
            continue

        # Score with Claude
        print(f"  Scoring [{company}] {title}...")
        try:
            score = _call_claude_score(title, company, content, profile)
        except (json.JSONDecodeError, Exception) as e:
            print(f"    Score error: {e} — skipping")
            continue

        fit = score.get("fit", 0)
        reason = score.get("reason", "")
        keep = fit >= fit_threshold

        if not keep:
            print(f"  SKIP fit={fit} — {reason}")
            continue

        # Write to queue
        queue_text = f"Company: {company}\nTitle: {title}\nURL: {apply_url}\n\n{content}"
        queue_file.write_text(queue_text, encoding="utf-8")

        # Pre-create results dir and store apply URL
        results_dir.mkdir(exist_ok=True)
        (results_dir / "apply_url.txt").write_text(apply_url, encoding="utf-8")

        print(f"  QUEUED fit={fit} — {reason}")
        queued += 1

    return queued
