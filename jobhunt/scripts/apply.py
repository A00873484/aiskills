"""
Automated job application filler using Playwright.

Usage:
    python scripts/apply.py <job_slug> [--submit]

    --submit   Actually click submit. Without it, the form is filled and
               a preview screenshot is saved for review.

Reads:
    results/<job_slug>/job_config.json   (apply_url, company)
    results/<job_slug>/resume.pdf        (uploaded as resume)
    config.json                          (personal details, Workday password)

Generic ATS handlers live in lib/ats.py.
Employer-specific handlers (hardcoded question IDs) live below — promote to
lib/ats.py once a handler proves reusable across multiple employers.
"""

import sys
import json
import os
from pathlib import Path

os.environ.setdefault("PYTHONUNBUFFERED", "1")
sys.stdout.reconfigure(line_buffering=True)
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

from lib.ats import APPLICANT, load_config, dismiss_popups, handle_verification, fill_workday

BASE_DIR = Path(__file__).parent.parent


def load_job(slug):
    path = BASE_DIR / "results" / slug / "job_config.json"
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# ── Employer-specific handlers ─────────────────────────────────────────────────
# Field IDs here are hardcoded to a specific employer's form instance.
# They will not work for other employers on the same ATS platform.

def fill_toast(page, resume_path: Path, submit: bool):
    """Slice / Toast embedded Greenhouse form."""

    def fill(selector, value):
        el = page.locator(selector).first
        el.click()
        el.fill(value)

    def select_by_text(selector, text):
        page.locator(selector).first.select_option(label=text)

    dismiss_popups(page)

    print("  Waiting for form to load...")
    page.wait_for_selector("#form_legal_first_name_2_0_0", state="visible", timeout=30000)
    page.locator("#form_legal_first_name_2_0_0").scroll_into_view_if_needed()

    print("  Filling: Legal First Name")
    fill("#form_legal_first_name_2_0_0", APPLICANT["first_name"])

    print("  Filling: Legal Last Name")
    fill("#form_legal_last_name_2_0_1", APPLICANT["last_name"])

    print("  Filling: Email")
    fill("#form_email_2_0_2", APPLICANT["email"])

    print("  Filling: Phone")
    # intl-tel-input country flag widget overlaps the field — bypass via JS
    page.evaluate(
        "(v) => { const el = document.getElementById('form_phone_2_0_3'); el.value = v; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); }",
        APPLICANT["phone"]
    )

    print("  Filling: Location")
    fill("#question_2_0_4_4_0", APPLICANT["location_ca"])

    print("  Filling: Postal Code")
    fill("#question_2_0_4_0_7", APPLICANT["postal_ca"])

    print("  Uploading: Resume")
    page.locator("#question_2_0_4_0_1").set_input_files(str(resume_path))
    page.wait_for_timeout(500)

    print("  Filling: LinkedIn")
    fill("#question_2_0_4_0_2", APPLICANT["linkedin"])

    print("  Selecting: Legally authorized to work in Canada")
    select_by_text("#question_2_0_4_0_4", "Yes")

    print("  Selecting: Sponsorship required")
    select_by_text("#question_2_0_4_0_5", "No")

    print("  Selecting: Privacy agreement")
    select_by_text("#question_2_0_4_0_6", "I agree")

    if submit:
        print("  Submitting form...")
        page.locator("#form_submit_2_0").click()
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        print("  Submitted. Final URL:", page.url)
        page.screenshot(path=str(resume_path.parent / "application_submitted.png"), full_page=True)
        print("  Screenshot saved to application_submitted.png")
        handle_verification(page, resume_path.parent)
    else:
        page.screenshot(path=str(resume_path.parent / "application_preview.png"), full_page=True)
        print("\n  Form filled. Preview screenshot saved to application_preview.png")
        print("  Run with --submit to actually submit.")


def fill_soloio(page, resume_path: Path, submit: bool):
    """Solo.io Greenhouse board — custom question IDs are specific to this employer."""

    def react_select(input_id: str, option_text: str):
        page.locator(f"#{input_id}").click()
        page.wait_for_selector('[role="option"]', timeout=3000)
        page.get_by_role("option", name=option_text).first.click()

    dismiss_popups(page)

    print("  Waiting for form to load...")
    page.wait_for_selector("#first_name", state="visible", timeout=30000)
    page.locator("#first_name").scroll_into_view_if_needed()

    print("  Filling: First Name")
    page.locator("#first_name").fill(APPLICANT["first_name"])

    print("  Filling: Last Name")
    page.locator("#last_name").fill(APPLICANT["last_name"])

    print("  Filling: Email")
    page.locator("#email").fill(APPLICANT["email"])

    print("  Selecting: Country")
    react_select("country", "United States")

    print("  Filling: Phone")
    # intl-tel-input widget overlaps the field — bypass via JS
    page.evaluate(
        "(v) => { const el = document.getElementById('phone'); el.value = v; el.dispatchEvent(new Event('input', {bubbles:true})); el.dispatchEvent(new Event('change', {bubbles:true})); }",
        APPLICANT["phone"]
    )

    print("  Uploading: Resume")
    page.locator("#resume").set_input_files(str(resume_path))
    page.wait_for_timeout(500)

    # Solo.io custom questions — IDs are specific to this employer's Greenhouse form
    print("  Selecting: Based in United States")
    react_select("question_8653711005", "Yes")

    print("  Selecting: Sponsorship required")
    react_select("question_8653712005", "No")

    print("  Selecting: Willing to travel twice/year")
    react_select("question_8653713005", "Yes")

    print("  Filling: LinkedIn")
    page.locator("#question_8653709005").fill(APPLICANT["linkedin"])

    # EEO voluntary questions — decline all
    for field_id in ["gender", "hispanic_ethnicity", "veteran_status", "disability_status"]:
        try:
            page.locator(f"#{field_id}").click(timeout=2000)
            page.wait_for_selector('[role="option"]', timeout=2000)
            for decline_text in ["Decline to Self Identify", "Decline", "I don't wish to answer", "Prefer not to say"]:
                try:
                    page.get_by_role("option", name=decline_text).first.click(timeout=1500)
                    break
                except Exception:
                    pass
        except Exception:
            pass

    if submit:
        print("  Submitting form...")
        page.get_by_role("button", name="Submit Application").click()
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        print("  Submitted. Final URL:", page.url)
        page.screenshot(path=str(resume_path.parent / "application_submitted.png"), full_page=True)
        print("  Screenshot saved to application_submitted.png")
        handle_verification(page, resume_path.parent)
    else:
        page.screenshot(path=str(resume_path.parent / "application_preview.png"), full_page=True)
        print("\n  Form filled. Preview screenshot saved to application_preview.png")
        print("  Run with --submit to actually submit.")


# ── ATS router ────────────────────────────────────────────────────────────────

ATS_HANDLERS = {
    "job-boards.greenhouse.io": fill_soloio,  # standard GH board — must come before greenhouse.io
    "toasttab.com":             fill_toast,
    "greenhouse.io":            fill_toast,   # other embedded Greenhouse forms (e.g. Slice)
    "myworkdayjobs.com":        fill_workday,
    "careers.lululemon.com":    fill_workday,
}


def get_handler(url: str):
    for domain, handler in ATS_HANDLERS.items():
        if domain in url:
            return handler
    return None


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    if not args:
        print("Usage: python scripts/apply.py <job_slug> [--submit]")
        sys.exit(1)

    slug = args[0]
    submit = "--submit" in args

    job = load_job(slug)
    apply_url = job.get("apply_url")
    if not apply_url:
        print(f"ERROR: no apply_url in results/{slug}/job_config.json")
        sys.exit(1)

    resume_path = BASE_DIR / "results" / slug / "resume.pdf"
    if not resume_path.exists():
        print(f"ERROR: resume not found at {resume_path}")
        sys.exit(1)

    handler = get_handler(apply_url)
    if not handler:
        print(f"ERROR: no handler for URL: {apply_url}")
        print("Supported ATS: " + ", ".join(ATS_HANDLERS.keys()))
        sys.exit(1)

    print(f"Applying to: {job['company']} ({slug})")
    print(f"URL:         {apply_url}")
    print(f"Resume:      {resume_path}")
    print(f"Mode:        {'SUBMIT' if submit else 'PREVIEW (use --submit to actually submit)'}")
    print()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)   # headed so you can watch
        ctx = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
        )
        page = ctx.new_page()
        print("Navigating to application form...")
        # Workday SPAs never fire networkidle — use domcontentloaded for them
        wait_strategy = "domcontentloaded" if "myworkdayjobs.com" in apply_url or "lululemon.com" in apply_url else "networkidle"
        page.goto(apply_url, wait_until=wait_strategy, timeout=45000)

        try:
            handler(page, resume_path, submit=submit)
        except PWTimeout as e:
            print(f"TIMEOUT: {e}")
            page.screenshot(path=str(resume_path.parent / "application_error.png"), full_page=True)
            print("Error screenshot saved.")
        except Exception as e:
            print(f"ERROR: {e}")
            page.screenshot(path=str(resume_path.parent / "application_error.png"), full_page=True)
            print("Error screenshot saved.")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
