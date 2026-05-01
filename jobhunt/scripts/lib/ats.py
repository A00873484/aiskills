"""
Permanent ATS automation library.

Contains generic, platform-wide handlers and shared utilities.
Employer-specific handlers (hardcoded question IDs, custom fields) live in apply.py.
Promote a handler here only once it's proven to work across multiple employers on the same platform.
"""

import json
import time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent  # scripts/lib → scripts → jobhunt


def load_config():
    with open(BASE_DIR / "config.json", encoding="utf-8") as f:
        return json.load(f)


APPLICANT = {
    "first_name":  "Daniel",
    "last_name":   "Engelhard",
    "email":       "danny.engelhard@gmail.com",
    "phone":       "7788392416",          # digits only — intl-tel-input handles formatting
    "linkedin":    "https://www.linkedin.com/in/daniel-engelhard-51ba278b/",

    # Canadian details
    "location_ca": "Burnaby, BC",
    "postal_ca":   "V5E0A1",

    # US details (sister's address, for US applications)
    "address_us":  "Unit A - 705 Forest Cir",
    "city_us":     "Lynden",
    "state_us":    "WA",
    "zip_us":      "98264",
    "location_us": "Lynden, WA",

    # Work authorization
    "authorized_ca": True,
    "authorized_us": True,
    "needs_sponsorship": False,
}


def dismiss_popups(page):
    """Dismiss common modal/popup patterns. Add new selectors here as new ATS sites are encountered."""
    POPUP_SELECTORS = [
        # Cookie consent
        "#consent_agree",
        "[id*='cookie'] button[class*='accept']",
        "[id*='cookie'] button[class*='agree']",
        "button[class*='cookie-accept']",
        "button[class*='accept-cookie']",
        # Generic close buttons on overlays / modals
        "[aria-label='Close']",
        "[aria-label='close']",
        "[aria-label='Dismiss']",
        ".modal-close",
        ".close-modal",
        "button[class*='modal'][class*='close']",
        "button[class*='close'][class*='modal']",
        # Chat / marketing widgets (Intercom, Drift, Zendesk)
        "#launcher",
        ".intercom-launcher-badge-frame",
        "[data-testid='close-button']",
    ]
    dismissed = []
    for sel in POPUP_SELECTORS:
        try:
            page.locator(sel).first.click(timeout=300)
            dismissed.append(sel)
        except Exception:
            pass
    if dismissed:
        print(f"  Dismissed popup(s): {', '.join(dismissed)}")
    else:
        print("  No popups detected.")


def handle_verification(page, result_dir: Path):
    """If a verification code page appears, poll for a code written to verify_code.txt."""
    try:
        page.wait_for_load_state("domcontentloaded", timeout=5000)
    except Exception:
        pass
    body = page.inner_text("body")

    if "validation code" not in body.lower() and "verify" not in body.lower():
        return True

    code_file = result_dir / "verify_code.txt"
    flag_file = result_dir / "need_verify.txt"

    flag_file.write_text("waiting", encoding="utf-8")
    print(f"\n  Email verification required.")
    print(f"  WAITING: Write the verification code to:")
    print(f"  {code_file}")
    print(f"  (polling every 3s for up to 120s...)")

    deadline = time.time() + 120
    code = None
    while time.time() < deadline:
        if code_file.exists():
            code = code_file.read_text(encoding="utf-8").strip()
            if code:
                code_file.unlink()
                flag_file.unlink(missing_ok=True)
                break
        time.sleep(3)

    if not code:
        page.screenshot(path=str(result_dir / "application_needs_verify.png"), full_page=True)
        print("  Timed out waiting for verification code.")
        return False

    print(f"  Got code: {code} — entering...")
    code_input = page.locator("input[type=text], input[type=number]").first
    code_input.fill(code)
    page.wait_for_timeout(300)
    page.get_by_role("button", name="VERIFY").click()
    try:
        page.wait_for_load_state("domcontentloaded", timeout=8000)
    except Exception:
        pass
    print("  Verified. Final URL:", page.url)
    page.screenshot(path=str(result_dir / "application_verified.png"), full_page=True)
    print("  Screenshot saved to application_verified.png")
    return True


def fill_workday(page, resume_path: Path, submit: bool):
    """Fill a standard Workday application form.

    Works for any myworkdayjobs.com employer — automation IDs are platform-standard.
    Steps: Apply → Apply Manually → Sign In → My Information → Save and Continue
    """
    cfg = load_config()
    wd_password = cfg.get("workday_password", "")

    def wd(automation_id: str):
        return page.locator(f'[data-automation-id="{automation_id}"]')

    def wd_input(form_field_id: str, value: str):
        inp = wd(form_field_id).locator("input").first
        inp.click()
        inp.fill(value)

    def wd_select_option(form_field_id: str, option_text: str):
        """Open a Workday combobox and pick an option by text."""
        container = wd(form_field_id)
        try:
            container.locator("button").first.click(timeout=3000)
        except Exception:
            container.click()
        page.wait_for_selector('[role="listbox"]', timeout=5000)
        # Type to filter for long lists (e.g. province picker)
        try:
            container.locator("input").first.fill(option_text[:4])
            page.wait_for_timeout(200)
        except Exception:
            pass
        page.get_by_role("option", name=option_text).first.click(timeout=8000, force=True)

    dismiss_popups(page)

    print("  Clicking Apply button...")
    for role, label in [("link", "Apply"), ("button", "Apply"), ("button", "Apply Now")]:
        try:
            page.get_by_role(role, name=label).first.click(timeout=5000)
            try:
                page.wait_for_load_state("domcontentloaded", timeout=8000)
            except Exception:
                pass
            break
        except Exception:
            pass

    print(f"  After Apply click — URL: {page.url}")

    for label in ["Apply Manually", "Continue", "Skip this step"]:
        try:
            page.get_by_role("button", name=label).first.click(timeout=4000)
            print(f"  Clicked modal: '{label}'")
            try:
                page.wait_for_load_state("domcontentloaded", timeout=6000)
            except Exception:
                pass
            break
        except Exception:
            pass

    try:
        wd("signInLink").click(timeout=5000)
        print("  Switched to Sign In panel")
        wd("email").first.fill(APPLICANT["email"])
        wd("password").first.fill(wd_password)
        signed_in = False
        for btn_id in ["signIn", "signInSubmitButton"]:
            try:
                wd(btn_id).click(timeout=3000)
                signed_in = True
                print(f"  Clicked sign-in submit: {btn_id}")
                break
            except Exception:
                pass
        if not signed_in:
            page.get_by_role("button", name="Sign In").last.click(timeout=3000)
            print("  Clicked Sign In by role")
        print(f"  After sign in — URL: {page.url}")
    except Exception as e:
        print(f"  Sign in skipped (may already be logged in): {e}")

    try:
        page.wait_for_selector('[data-automation-id="applyFlowMyInfoPage"]', timeout=15000)
        print("  My Information page loaded")
    except Exception:
        print(f"  WARNING: My Information not detected — URL: {page.url}")

    print("  Uploading: Resume")
    try:
        page.locator('input[type="file"]').first.set_input_files(str(resume_path))
        page.wait_for_timeout(1000)
        print("  Resume uploaded")
    except Exception:
        print("  WARNING: resume upload step not found — skipping")

    print("  Filling: First Name")
    try:
        wd_input("formField-legalName--firstName", APPLICANT["first_name"])
    except Exception as e:
        print(f"  WARNING first name: {e}")

    print("  Filling: Last Name")
    try:
        wd_input("formField-legalName--lastName", APPLICANT["last_name"])
    except Exception as e:
        print(f"  WARNING last name: {e}")

    print("  Filling: City")
    try:
        wd_input("formField-city", "Burnaby")
    except Exception as e:
        print(f"  WARNING city: {e}")

    print("  Selecting: Province")
    try:
        wd_select_option("formField-countryRegion", "British Columbia")
    except Exception as e:
        print(f"  WARNING province: {e}")

    print("  Filling: Postal Code")
    try:
        wd_input("formField-postalCode", APPLICANT["postal_ca"])
    except Exception as e:
        print(f"  WARNING postal: {e}")

    print("  Selecting: Phone Device Type")
    try:
        wd_select_option("formField-phoneType", "Mobile")
    except Exception as e:
        print(f"  WARNING phone type: {e}")

    print("  Filling: Phone Number")
    try:
        wd_input("formField-phoneNumber", APPLICANT["phone"])
    except Exception as e:
        print(f"  WARNING phone: {e}")

    print("  Selecting: How Did You Hear About Us")
    try:
        src_container = wd("formField-source").locator('[data-automation-id="multiselectInputContainer"]')
        src_container.click(timeout=5000)
        page.wait_for_selector('[role="listbox"]', timeout=5000)
        page.wait_for_timeout(200)
        all_nodes = page.locator('[data-automation-id="promptLeafNode"]')
        available = all_nodes.all_text_contents()
        print(f"  Source options: {available}")
        preference = ["LinkedIn", "Job Board", "Appcast", "Social Networking", "Other"]
        chosen_idx, chosen_text = None, None
        for want in preference:
            for i, opt_text in enumerate(available):
                if want.lower() in opt_text.lower():
                    chosen_idx, chosen_text = i, opt_text
                    break
            if chosen_idx is not None:
                break
        if chosen_idx is None and available:
            chosen_idx, chosen_text = 0, available[0]
        if chosen_idx is not None:
            # Arrow keys + Space are more reliable than mouse clicks in Workday multiselects
            for _ in range(chosen_idx + 1):
                page.keyboard.press("ArrowDown")
                page.wait_for_timeout(100)
            page.keyboard.press("Space")
            page.wait_for_timeout(200)
            print(f"  Selected source: {chosen_text}")
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
    except Exception as e:
        print(f"  WARNING source: {e}")

    print("  Selecting: Previously worked here = No")
    try:
        wd("formField-candidateIsPreviousWorker").scroll_into_view_if_needed()
        # Regular click doesn't fire React events — use JS dispatch
        page.evaluate("""() => {
            const inp = document.querySelector('[name="candidateIsPreviousWorker"][value="false"]');
            if (!inp) return;
            const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'checked').set;
            setter.call(inp, true);
            inp.dispatchEvent(new Event('click', {bubbles: true}));
            inp.dispatchEvent(new Event('change', {bubbles: true}));
        }""")
    except Exception as e:
        print(f"  WARNING previous worker: {e}")

    print("  Clicking: Save and Continue")
    try:
        wd("pageFooterNextButton").click(timeout=5000)
        try:
            page.wait_for_load_state("domcontentloaded", timeout=10000)
        except Exception:
            pass
        print(f"  After Save and Continue — URL: {page.url}")
    except Exception as e:
        print(f"  WARNING: Save and Continue: {e}")

    if submit:
        page.screenshot(path=str(resume_path.parent / "application_step2.png"), full_page=True)
        print("  Screenshot saved (step 2). Workday is multi-step — manual review needed.")
    else:
        page.screenshot(path=str(resume_path.parent / "application_preview.png"), full_page=True)
        print("\n  My Information filled. Preview screenshot saved.")
        print("  Run with --submit to actually submit.")
