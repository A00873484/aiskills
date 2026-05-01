from __future__ import annotations
import urllib.parse
from playwright.async_api import Page
from playwright_lib.pages.base import BasePage


_EXTRACT_JD_JS = """() => {
    const selectors = [
        '.jobs-description__content',
        '.jobs-description-content__text',
        '#job-details',
        '.jobs-box__html-content',
        '.description__text',
        '.show-more-less-html__markup',
    ];
    for (const sel of selectors) {
        const el = document.querySelector(sel);
        if (el && el.innerText.trim()) return el.innerText.trim();
    }
    return '';
}"""

_EXTRACT_JS = """() => {
    const selectors = [
        '.job-card-container',
        '.jobs-search-results__list-item',
        '[data-occludable-job-id]',
        '.base-card',
    ];
    let items = [];
    for (const sel of selectors) {
        const found = document.querySelectorAll(sel);
        if (found.length > 0) { items = found; break; }
    }
    return Array.from(items).slice(0, 25).map(item => {
        const titleEl = item.querySelector(
            '[aria-label], .job-card-list__title, .base-card__full-link, a.job-card-container__link, .base-search-card__title'
        );
        const companyEl = item.querySelector(
            '.artdeco-entity-lockup__subtitle span, .job-card-container__company-name, .base-search-card__subtitle'
        );
        const locationEl = item.querySelector(
            '.job-card-container__metadata-item, .base-search-card__metadata, .artdeco-entity-lockup__caption'
        );
        const linkEl = item.querySelector('a[href*="/jobs/view/"]');
        const jobId = item.getAttribute('data-occludable-job-id') || item.getAttribute('data-job-id') || '';
        const rawUrl = linkEl ? linkEl.href : '';
        const cleanUrl = rawUrl ? rawUrl.split('?')[0] : (jobId ? `https://www.linkedin.com/jobs/view/${jobId}` : '');
        return {
            title: titleEl?.innerText?.trim() || titleEl?.getAttribute('aria-label')?.trim() || '',
            company: companyEl?.innerText?.trim() || '',
            location: locationEl?.innerText?.trim() || '',
            url: cleanUrl,
            job_id: jobId,
        };
    }).filter(j => j.title && j.url);
}"""


class LinkedInPage(BasePage):
    def __init__(self, page: Page) -> None:
        super().__init__(page)

    def _build_search_url(self, query: str, days_back: int = 14) -> str:
        encoded = urllib.parse.quote_plus(query)
        seconds = days_back * 86400
        return f"https://www.linkedin.com/jobs/search/?keywords={encoded}&f_TPR=r{seconds}&sortBy=DD"

    async def _check_auth_wall(self) -> bool:
        url = self.page.url
        title = await self.page.title()
        return "authwall" in url or "login" in url or "Sign In" in title

    async def run_searches(self, queries: list[str], days_back: int = 14) -> list[dict]:
        results: list[dict] = []

        for query in queries:
            url = self._build_search_url(query, days_back)
            print(f"  Searching: {query!r}")
            try:
                if not await self.safe_goto(url, timeout=30_000):
                    print("    Failed to navigate to search URL")
                    continue
                await self.page.wait_for_timeout(3000)

                if await self._check_auth_wall():
                    print("    WARNING: LinkedIn not logged in / authwall hit")
                    continue

                jobs: list[dict] = await self.evaluate_safe(_EXTRACT_JS) or []
                print(f"    {len(jobs)} job(s) extracted")
                for job in jobs:
                    job["source"] = "linkedin"
                results.extend(jobs)
            except Exception as e:
                print(f"    Error on query {query!r}: {e}")

        # deduplicate by URL
        seen: dict[str, dict] = {}
        for job in results:
            url = job.get("url", "")
            if url and url not in seen:
                seen[url] = job
        unique = list(seen.values())

        print(f"\n  Fetching descriptions for {len(unique)} unique job(s)...")
        for i, job in enumerate(unique, 1):
            try:
                if not await self.safe_goto(job["url"], timeout=20_000):
                    job["content"] = ""
                    print(f"  [{i}/{len(unique)}] {job.get('title')}: failed to navigate")
                    continue
                await self.page.wait_for_timeout(1500)
                content = await self.evaluate_safe(_EXTRACT_JD_JS) or ""
                job["content"] = content
                status = f"{len(content)} chars" if content else "no content found"
                print(f"  [{i}/{len(unique)}] {job.get('company')} — {job.get('title')}: {status}")
            except Exception as e:
                print(f"  [{i}/{len(unique)}] {job.get('title')}: error — {e}")
                job["content"] = ""

        return unique
