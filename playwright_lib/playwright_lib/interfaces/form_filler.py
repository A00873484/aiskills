from typing import Protocol
from playwright_lib.result import AutomationResult
from playwright_lib.manager import BrowserManager


class FormFiller(Protocol):
    async def fill(self, input: dict, manager: BrowserManager) -> AutomationResult: ...
