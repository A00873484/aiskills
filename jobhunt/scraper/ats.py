"""Poll Greenhouse, Ashby, and Lever ATS job boards for new postings."""
import json
import re
import urllib.request
import urllib.error


def fetch_greenhouse(slug: str) -> list[dict]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs?content=true"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        jobs = []
        for job in data.get("jobs", []):
            jobs.append({
                "id": str(job["id"]),
                "title": job["title"],
                "url": job.get("absolute_url", ""),
                "location": job.get("location", {}).get("name", ""),
                "content": _strip_html(job.get("content", "")),
            })
        return jobs
    except Exception as e:
        print(f"    Greenhouse {slug}: {e}")
        return []


def fetch_lever(slug: str) -> list[dict]:
    url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        jobs = []
        for job in data:
            sections = job.get("lists", [])
            content_parts = []
            for s in sections:
                if isinstance(s, dict):
                    content_parts.append(f"{s.get('text', '')}: {s.get('content', '')}")
            content = "\n".join(content_parts) or job.get("descriptionPlain", "")
            jobs.append({
                "id": job["id"],
                "title": job["text"],
                "url": job.get("hostedUrl", f"https://jobs.lever.co/{slug}/{job['id']}"),
                "location": job.get("categories", {}).get("location", ""),
                "content": _strip_html(content),
            })
        return jobs
    except Exception as e:
        print(f"    Lever {slug}: {e}")
        return []


def fetch_ashby(slug: str) -> list[dict]:
    url = f"https://jobs.ashbyhq.com/{slug}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
        match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            print(f"    Ashby {slug}: could not find __NEXT_DATA__")
            return []
        data = json.loads(match.group(1))
        page_props = data.get("props", {}).get("pageProps", {})
        postings = (
            page_props.get("jobPostings")
            or page_props.get("jobs")
            or page_props.get("initialData", {}).get("jobPostings", [])
            or []
        )
        jobs = []
        for job in postings:
            job_id = job.get("id", "")
            location = (
                job.get("locationName")
                or job.get("primaryLocation", {}).get("locationName", "")
                or ""
            )
            jobs.append({
                "id": job_id,
                "title": job.get("title", ""),
                "url": f"https://jobs.ashbyhq.com/{slug}/{job_id}",
                "location": location,
                "content": _strip_html(job.get("descriptionHtml", "") or job.get("description", "")),
            })
        return jobs
    except Exception as e:
        print(f"    Ashby {slug}: {e}")
        return []


def _strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&amp;", "&", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"\s{2,}", " ", text)
    return text.strip()


_FETCHERS = {
    "greenhouse": fetch_greenhouse,
    "lever": fetch_lever,
    "ashby": fetch_ashby,
}


def poll(target_companies: list[dict]) -> list[dict]:
    """Poll all configured ATS boards. Returns all jobs with 'company' field added."""
    all_jobs = []
    for company in target_companies:
        name = company["company"]
        ats = company["ats"]
        slug = company["slug"]
        print(f"  {name} ({ats})...")
        fetcher = _FETCHERS.get(ats)
        if not fetcher:
            print(f"    Unknown ATS type: {ats}")
            continue
        jobs = fetcher(slug)
        for job in jobs:
            job["company"] = name
            job["ats"] = ats
        all_jobs.extend(jobs)
        print(f"    {len(jobs)} posting(s) found")
    return all_jobs
