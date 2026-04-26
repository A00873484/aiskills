import pytest
from unittest.mock import AsyncMock, MagicMock
from playwright_lib.manager import BrowserManager
from playwright_lib.pages.base import BasePage


@pytest.fixture
def mock_page():
    page = AsyncMock()
    page.url = "https://www.linkedin.com/jobs/search/"
    page.title = AsyncMock(return_value="LinkedIn Jobs")
    page.evaluate = AsyncMock(return_value=[])
    page.goto = AsyncMock()
    page.wait_for_timeout = AsyncMock()
    page.wait_for_selector = AsyncMock(return_value=None)
    return page


@pytest.fixture
def mock_manager(mock_page):
    mgr = MagicMock(spec=BrowserManager)
    mgr.connect = AsyncMock()
    mgr.get_page = AsyncMock(return_value=mock_page)
    mgr.new_page = AsyncMock(return_value=mock_page)
    mgr.close = AsyncMock()
    return mgr
