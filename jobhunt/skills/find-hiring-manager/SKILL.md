---
name: find-hiring-manager
description: Use this skill when the user wants to find the hiring manager, recruiter, or decision-maker for a job posting or company. Triggers on phrases like "find the hiring manager", "who is hiring for", "find the recruiter at", "who should I reach out to", "find the person who posted this job", "find the team lead at", or when the user has a job posting and wants to identify who to contact.
version: 1.0.0
---

# Find Hiring Manager Skill

Identify the most likely hiring manager or recruiter for a role so the user can send a targeted outreach message.

## Process

### Step 1 — Extract Company + Role Context

From the job posting or user input, identify:
- Company name (exact legal name, not abbreviation)
- Role title
- Team or department (if mentioned)
- Location of the role

### Step 2 — Search for the Hiring Manager

Work through these strategies in order, using WebSearch:

#### Strategy A: Find who posted the job on LinkedIn
```
site:linkedin.com "[Company Name]" hiring "[role title]" OR "we're looking for" OR "join our team"
```

#### Strategy B: Find the team lead / engineering manager / department head
```
site:linkedin.com/in "[Company Name]" "Head of Engineering" OR "VP of Engineering" OR "Engineering Manager"
```
Adjust title to match the role's department (Product, Design, Marketing, etc.)

#### Strategy C: Find the recruiter at the company
```
site:linkedin.com/in "[Company Name]" recruiter OR "talent acquisition" OR "recruiting"
```

#### Strategy D: Search Twitter/X and company blog
```
"[Company Name]" hiring "[role title]" site:twitter.com OR site:x.com
"[Company Name]" "we're hiring" "[role title]"
```

#### Strategy E: Check the company's team page
- Look for `[company].com/team`, `[company].com/about`, `[company].com/people`
- Search: `site:[company].com "team" OR "people" OR "about"`

### Step 3 — Build a Candidate List

For each person found, collect:

| Field | Details |
|-------|---------|
| **Name** | Full name |
| **Title** | Current role at company |
| **LinkedIn URL** | Profile link |
| **Relevance** | Why they're likely the right person |
| **Confidence** | High / Medium / Low |

Rank by confidence. Prefer:
1. The person who posted the job (highest confidence)
2. Direct manager for the role (e.g., Engineering Manager if hiring SWE)
3. Department head / VP
4. In-house recruiter / talent acquisition

### Step 4 — Find Contact Information (Optional)

If the user wants to email directly (not just LinkedIn), search:
```
"[First Name] [Last Name]" "[Company Name]" email
"[First Name] [Last Name]" "@[company].com"
```

Common email patterns to suggest:
- `firstname@company.com`
- `firstname.lastname@company.com`
- `f.lastname@company.com`

Verify using Hunter.io or Clearbit if available.

### Step 5 — Output

Present:
1. **Top pick** — the most likely hiring manager with confidence level and why
2. **Backup contacts** — 1-2 alternates
3. **LinkedIn profile links** for each
4. **Suggested approach** — direct message, connection request, or email

Then prompt: "Want me to draft a personalized outreach message? Use `/reachout` with this person's name and the job posting."
