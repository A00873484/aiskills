---
name: job-search
description: Use this skill when the user wants to find job postings, search for jobs on LinkedIn, look for open roles, discover job opportunities, or browse positions matching their background. Triggers on phrases like "find jobs", "search for jobs", "what jobs are available", "job postings for", "look for roles", "find openings", or when the user describes job criteria they want to search for.
version: 1.0.0
---

# Job Search Skill

Help the user find relevant job postings on LinkedIn by building smart search queries, extracting key details from postings, and organizing results for action.

## Process

### Step 1 — Understand Their Target

If the user hasn't provided it, ask for:
- **Role/title** (e.g., "Software Engineer", "Product Manager")
- **Industry or domain** (e.g., fintech, healthcare, SaaS)
- **Location or remote preference**
- **Experience level** (entry, mid, senior, staff)
- **Company size preference** (startup, mid-size, enterprise)

### Step 2 — Build LinkedIn Search URLs

Construct targeted LinkedIn job search URLs using this pattern:

```
https://www.linkedin.com/jobs/search/?keywords=KEYWORDS&location=LOCATION&f_E=EXPERIENCE&f_WT=WORK_TYPE
```

Experience level codes:
- `1` = Internship
- `2` = Entry level
- `3` = Associate
- `4` = Mid-Senior level
- `5` = Director
- `6` = Executive

Work type codes:
- `1` = On-site
- `2` = Remote
- `3` = Hybrid

Also suggest **Boolean search strings** the user can paste into LinkedIn's search bar:
```
"job title" AND ("company type" OR "industry") AND ("skill 1" OR "skill 2")
```

### Step 3 — Supplement with Web Search

Use WebSearch to find recently posted jobs that LinkedIn may surface slowly:
- Search: `site:linkedin.com/jobs "[role title]" "[location or remote]" [current year]`
- Search: `"[Company Name]" is hiring "[role]" linkedin`
- Search job boards: `"[role]" [industry] jobs [location] -staffing -agency`

### Step 4 — Extract and Summarize Job Postings

When the user pastes a job posting URL or text, extract:

| Field | Details |
|-------|---------|
| **Company** | Name, size, industry, funding stage |
| **Role** | Title, level, team |
| **Location** | City / Remote / Hybrid |
| **Key Requirements** | Top 5 must-haves |
| **Nice-to-haves** | Preferred qualifications |
| **Red flags** | Vague comp, high turnover signals, unrealistic requirements |
| **Opportunity signals** | Growth stage, recent funding, team expansion |
| **Application link** | Direct URL |

### Step 5 — Score and Prioritize

Rate each posting on a 1-5 scale across:
- **Fit**: How well does the user's background match?
- **Opportunity**: Company trajectory, role impact
- **Comp potential**: Signals from posting + Glassdoor/Levels.fyi data

Recommend a **shortlist** of top 3-5 to pursue first.

## Output Format

Present results as a prioritized table, then expand on each top pick with full details and suggested next steps (apply + reach out to hiring manager).

## Tips for Better Results

- LinkedIn's "Easy Apply" filters out many great roles — always check company career pages directly
- Sort by "Most Recent" not "Most Relevant" on LinkedIn to catch fresh postings
- Jobs posted < 3 days ago get far less competition
- Use the `/find-hiring-manager` skill after identifying a good role
