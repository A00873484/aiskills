from playwright_lib.result import AutomationResult
from playwright_lib.manager import BrowserManager


class BrowserUseFormFiller:
    """
    FormFiller that delegates to a browser-use Agent (Claude-driven).
    manager is accepted for interface consistency but not used —
    browser-use manages its own Playwright session.
    """

    async def fill(self, input: dict, manager: BrowserManager) -> AutomationResult:
        task: str = input.get("task", "")
        api_key: str = input.get("api_key", "")
        model: str = input.get("model", "claude-sonnet-4-6")

        if not task:
            return AutomationResult.fail("No task provided", input=input)
        if not api_key:
            return AutomationResult.fail("No api_key provided", input=input)

        try:
            from browser_use import Agent, ChatAnthropic  # type: ignore[import]
        except ImportError as e:
            return AutomationResult.fail(
                f"browser-use not installed: {e}. Run: uv sync --extra browser-use",
                input=input,
            )

        llm = ChatAnthropic(model=model, api_key=api_key)
        agent = Agent(task=task, llm=llm)
        await agent.run()
        return AutomationResult.ok({"status": "form_filled"}, input=input)
