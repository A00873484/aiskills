import pytest
from playwright_lib.scrapers.linkedin import LinkedInScraper
from playwright_lib.result import AutomationResult


@pytest.mark.asyncio
async def test_scrape_no_queries_returns_fail(mock_manager):
    result = await LinkedInScraper().scrape({"queries": []}, mock_manager)
    assert not result.success
    assert result.error == "No queries provided"


@pytest.mark.asyncio
async def test_scrape_returns_jobs(mock_page, mock_manager):
    mock_page.evaluate.return_value = [
        {"title": "Engineer", "company": "Acme", "location": "Remote", "url": "https://linkedin.com/jobs/view/1", "job_id": "1"}
    ]
    result = await LinkedInScraper().scrape({"queries": ["python engineer"]}, mock_manager)
    assert result.success
    assert len(result.output["jobs"]) == 1
    assert result.output["jobs"][0]["title"] == "Engineer"


@pytest.mark.asyncio
async def test_scrape_echoes_input(mock_manager):
    input_data = {"queries": [], "days_back": 7}
    result = await LinkedInScraper().scrape(input_data, mock_manager)
    assert result.input == input_data


@pytest.mark.asyncio
async def test_scrape_authwall_skips_query(mock_page, mock_manager):
    mock_page.url = "https://www.linkedin.com/authwall"
    mock_page.title = lambda: "Sign In"
    result = await LinkedInScraper().scrape({"queries": ["engineer"]}, mock_manager)
    assert result.success
    assert result.output["jobs"] == []
