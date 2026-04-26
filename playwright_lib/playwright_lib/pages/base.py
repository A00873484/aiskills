from __future__ import annotations
from typing import Any
from playwright.async_api import Page


class BasePage:
    def __init__(self, page: Page) -> None:
        self.page = page

    async def safe_goto(self, url: str, *, timeout: int = 30_000) -> bool:
        try:
            await self.page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            return True
        except Exception:
            return False

    async def evaluate_safe(self, js: str) -> Any:
        try:
            return await self.page.evaluate(js)
        except Exception:
            return None

    async def wait_and_get_text(self, selector: str, timeout: int = 5_000) -> str | None:
        try:
            el = await self.page.wait_for_selector(selector, timeout=timeout)
            if el:
                return await el.inner_text()
        except Exception:
            pass
        return None
