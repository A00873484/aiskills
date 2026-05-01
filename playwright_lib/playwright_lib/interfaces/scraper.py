from typing import Protocol
from playwright_lib.result import AutomationResult
from playwright_lib.manager import BrowserManager


class Scraper(Protocol):
    async def scrape(self, input: dict, manager: BrowserManager) -> AutomationResult: ...
