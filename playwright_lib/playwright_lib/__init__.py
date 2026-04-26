from __future__ import annotations
from typing import Any
from playwright_lib.result import AutomationResult
from playwright_lib.manager import BrowserManager
from playwright_lib.interfaces.scraper import Scraper
from playwright_lib.interfaces.form_filler import FormFiller

__all__ = ["AutomationResult", "BrowserManager", "Scraper", "FormFiller", "run_automation"]


async def run_automation(
    automation: Scraper | FormFiller,
    input: dict[str, Any],
    *,
    manager: BrowserManager | None = None,
) -> AutomationResult:
    """
    Run a Scraper or FormFiller automation and guarantee BrowserManager cleanup.
    Pass an existing manager to reuse a browser session across multiple calls.
    """
    owns_manager = manager is None
    mgr = manager or BrowserManager()
    try:
        if hasattr(automation, "scrape"):
            return await automation.scrape(input, mgr)  # type: ignore[union-attr]
        return await automation.fill(input, mgr)  # type: ignore[union-attr]
    except Exception as exc:
        return AutomationResult.fail(error=str(exc), input=input)
    finally:
        if owns_manager:
            await mgr.close()
