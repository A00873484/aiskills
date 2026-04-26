import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from playwright_lib.form_fillers.browser_use import BrowserUseFormFiller
from playwright_lib.result import AutomationResult


@pytest.mark.asyncio
async def test_fill_no_task_returns_fail(mock_manager):
    result = await BrowserUseFormFiller().fill({"api_key": "key"}, mock_manager)
    assert not result.success
    assert result.error == "No task provided"


@pytest.mark.asyncio
async def test_fill_no_api_key_returns_fail(mock_manager):
    result = await BrowserUseFormFiller().fill({"task": "fill the form"}, mock_manager)
    assert not result.success
    assert result.error == "No api_key provided"


@pytest.mark.asyncio
async def test_fill_success(mock_manager):
    mock_agent = MagicMock()
    mock_agent.run = AsyncMock()

    with patch.dict("sys.modules", {"browser_use": MagicMock(Agent=MagicMock(return_value=mock_agent), ChatAnthropic=MagicMock())}):
        result = await BrowserUseFormFiller().fill(
            {"task": "fill the form", "api_key": "test-key"}, mock_manager
        )

    assert result.success
    assert result.output["status"] == "form_filled"
