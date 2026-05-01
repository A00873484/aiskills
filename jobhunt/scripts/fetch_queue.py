"""
Scrape job postings from URLs in queue/queue.txt.

Usage:
    python scripts/fetch_queue.py

Reads:  queue/queue.txt   (one URL per line; blank lines and # lines skipped)
Writes: queue/<slug>.txt  (title + full description, ready for process_queue.py)

Successfully scraped URLs are commented out in queue.txt automatically.
"""

import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

BASE_DIR = Path(__file__).parent.parent
QUEUE_DIR = BASE_DIR / "queue"
QUEUE_FILE = QUEUE_DIR / "queue.txt"


# ── Slug generation ───────────────────────────────────────────────────────────

def make_slug(url: str) -> str:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    parts = host.split(".")

    if "myworkdayjobs" in host:
        company = parts[0]
    elif "greenhouse.io" in host:
        path_parts = [p for p in parsed.path.split("/") if p]
        company = path_parts[0] if path_parts else "greenhouse"
    elif "breezy.hr" in host:
        company = parts[0]
    elif len(parts) >= 2:
        # careers.lululemon.com → lululemon, mastercard.com → mastercard
        company = next((p for p in reversed(parts[:-1]) if p not in ("careers", "www", "jobs", "apply")), parts[0])
    else:
        company = parts[0] if parts else "job"

    path = parsed.path
    path = re.sub(r"[A-Z]{2,}\d{5,}", "", path)   # strip IDs like MASRUSR276631
    path = re.sub(r"\d{5,}", "", path)              # strip numeric IDs
    words = re.split(r"[/_\-\s]+", path)
    skip = {"job", "jobs", "careers", "career", "ext", "apply", "en", "us",
            "ca", "canada", "amer", "autofillwithresume", "externalenus",
            "external", "career", "site", "listing"}
    words = [w.lower() for w in words if len(w) > 2 and w.lower() not in skip]
    title_slug = "-".join(words[:5])

    slug = f"{company}-{title_slug}" if title_slug else company
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:60]


# ── Per-ATS text extractors ───────────────────────────────────────────────────

def extract_workday(page) -> tuple[str, str]:
    """Workday SPA — wait for job description panel."""
    page.wait_for_selector('[data-automation-id="jobPostingDescription"]', timeout=20000)
    title = page.locator('[data-automation-id="jobPostingHeader"]').first.inner_text(timeout=5000)
    body = page.locator('[data-automation-id="jobPostingDescription"]').first.inner_text(timeout=5000)
    return title.strip(), body.strip()


def extract_greenhouse(page) -> tuple[str, str]:
    """Standard Greenhouse board (job-boards.greenhouse.io)."""
    page.wait_for_selector("#content", timeout=20000)
    title = page.locator("h1").first.inner_text(timeout=5000)
    body = page.locator("#content").inner_text(timeout=5000)
    return title.strip(), body.strip()


def extract_greenhouse_embed(page) -> tuple[str, str]:
    """Embedded Greenhouse form (slice.careers, etc.) — uses gh_jid param."""
    page.wait_for_selector(".job-post", timeout=20000)
    title = page.locator("h1").first.inner_text(timeout=5000)
    body = page.locator(".job-post").inner_text(timeout=5000)
    return title.strip(), body.strip()


def extract_generic(page) -> tuple[str, str]:
    """Best-effort fallback: try common job description containers."""
    selectors = [
        ".job-description", ".jobDescription", "#job-description",
        "[class*='job-description']", "[class*='jobDescription']",
        "[id*='job-description']", "article", "main",
    ]
    title = ""
    try:
        title = page.locator("h1").first.inner_text(timeout=3000)
    except Exception:
        pass

    for sel in selectors:
        try:
            text = page.locator(sel).first.inner_text(timeout=3000)
            if len(text) > 200:
                return title.strip(), text.strip()
        except Exception:
            continue

    # Last resort: full body text
    body = page.inner_text("body")
    return title.strip(), body.strip()


def get_extractor(url: str):
    if "myworkdayjobs.com" in url or "careers.lululemon.com" in url:
        return extract_workday, "domcontentloaded"
    if "job-boards.greenhouse.io" in url:
        return extract_greenhouse, "networkidle"
    if "greenhouse.io" in url or "gh_jid=" in url:
        return extract_greenhouse_embed, "networkidle"
    return extract_generic, "networkidle"


# ── Queue file helpers ────────────────────────────────────────────────────────

def read_queue() -> list[str]:
    return QUEUE_FILE.read_text(encoding="utf-8").splitlines()


def comment_out(url: str):
    """Replace the URL line with a commented-out version."""
    lines = read_queue()
    new_lines = []
    for line in lines:
        if line.strip() == url:
            new_lines.append(f"# done: {line}")
        else:
            new_lines.append(line)
    QUEUE_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    lines = read_queue()
    urls = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]

    if not urls:
        print("No URLs in queue/queue.txt — add some and re-run.")
        return

    print(f"Found {len(urls)} URL(s) to process.\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )

        for url in urls:
            slug = make_slug(url)
            out_file = QUEUE_DIR / f"{slug}.txt"
            print(f"Scraping: {url}")
            print(f"  Slug:    {slug}")

            extractor, wait_strategy = get_extractor(url)
            page = ctx.new_page()
            try:
                page.goto(url, wait_until=wait_strategy, timeout=45000)
                page.wait_for_timeout(2000)

                title, body = extractor(page)

                if not body or len(body) < 100:
                    print(f"  WARNING: extracted text too short ({len(body)} chars) — skipping")
                    page.close()
                    continue

                content = f"{url}\n\n{title}\n\n{body}\n"
                out_file.write_text(content, encoding="utf-8")
                print(f"  Written: queue/{slug}.txt  ({len(body)} chars)")
                comment_out(url)

            except PWTimeout:
                print(f"  TIMEOUT — skipping")
            except Exception as e:
                print(f"  ERROR: {e} — skipping")
            finally:
                page.close()

        browser.close()

    print("\nDone. Run process_queue.py next.")


if __name__ == "__main__":
    main()
