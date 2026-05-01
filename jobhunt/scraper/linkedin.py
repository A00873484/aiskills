import asyncio
from playwright_lib import run_automation
from playwright_lib.manager import BrowserManager
from playwright_lib.scrapers.linkedin import LinkedInScraper

CHROME_EXE = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PROFILE_DIR = r"C:\Users\danny\AppData\Local\Google\Chrome\User Data"


def scrape(queries: list[str]) -> list[dict]:
    if not queries:
        print("  No LinkedIn search queries configured.")
        return []
    mgr = BrowserManager(chrome_exe=CHROME_EXE, profile_dir=PROFILE_DIR)
    result = asyncio.run(run_automation(LinkedInScraper(), {"queries": queries}, manager=mgr))
    if result.success:
        return result.output.get("jobs", [])
    print(f"  LinkedIn scrape failed: {result.error}")
    return []
