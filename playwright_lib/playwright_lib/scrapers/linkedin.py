from playwright_lib.result import AutomationResult
from playwright_lib.manager import BrowserManager
from playwright_lib.pages.linkedin import LinkedInPage


class LinkedInScraper:
    async def scrape(self, input: dict, manager: BrowserManager) -> AutomationResult:
        queries: list[str] = input.get("queries", [])
        days_back: int = input.get("days_back", 14)

        if not queries:
            return AutomationResult.fail("No queries provided", input=input)

        page = await manager.get_page()
        lp = LinkedInPage(page)
        jobs = await lp.run_searches(queries, days_back)
        return AutomationResult.ok({"jobs": jobs}, input=input)
