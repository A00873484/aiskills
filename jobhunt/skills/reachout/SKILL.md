---
name: reachout
description: Use this skill when the user wants to write an outreach message, draft a LinkedIn message, craft a cold message to a hiring manager or recruiter, write a connection request, compose a follow-up message, or create a personalized note for a job application. Triggers on phrases like "write an outreach", "draft a message to the hiring manager", "help me reach out", "write a cold message", "draft a LinkedIn note", "follow up on my application", or "write a connection request".
version: 1.0.0
---

# Reachout Skill

Draft a short, personalized, and compelling outreach message that will actually stand out — not a generic template.

## Philosophy

Most outreach messages fail because they:
- Lead with "I'm very interested in your company" (self-centered)
- Are too long (nobody reads past 3 sentences in a cold DM)
- Sound like a template
- Ask for too much (a job, a referral, a call)

A great message:
- Is **short** (under 100 words for LinkedIn DM, under 200 for email)
- Leads with **specific value or connection** — something that proves you did your homework
- Ends with **one small, easy ask** (not "can you get me a job?")
- Feels like a **human wrote it**, not a bot

## Process

### Step 1 — Gather Context

Ask the user for (if not already provided):
- **Their background**: 2-3 sentences about who they are, key skills/experience
- **The role**: Job title and company
- **The recipient**: Name, title, and anything known about them
- **Unique angle**: Is there something specific that connects user → this company? (mutual connection, used the product, followed the person's work, attended their talk, etc.)
- **Message type**: LinkedIn DM, connection request note (300 char limit), cold email, or follow-up

### Step 2 — Research the Recipient (if not already done)

Use WebSearch to find:
- Recent LinkedIn posts, articles, or talks by this person
- News about the company (funding, product launch, expansion)
- Any shared interests, background, or alma mater
- The company's current challenges or priorities

This research is the source of the "specific hook" that makes the message personal.

### Step 3 — Craft the Message

#### For LinkedIn Connection Request (≤300 characters)
Structure:
1. **Specific hook** (1 sentence — a real observation, not flattery)
2. **Who you are** (1 sentence — most relevant credential)
3. **Soft ask** (connect / chat briefly)

Example:
> "Saw your post on scaling Postgres for high-write workloads — we tackled something similar at [Company]. I'm exploring backend roles and would love to connect."

#### For LinkedIn DM (≤100 words)
Structure:
1. **Hook** — specific observation about their work, company news, or shared connection
2. **Credibility** — one concrete thing you've done that's relevant
3. **Ask** — a small, easy yes/no question

Example:
> "Hi [Name] — I noticed [Company] just raised a Series B and is expanding the data platform team. At [Previous Company] I built a real-time ingestion pipeline that cut latency by 40%.
>
> I'd love to hear what the team is focused on for the next 6 months — would a quick 15-min chat work?"

#### For Cold Email (≤200 words)
Structure:
- **Subject**: Specific and curiosity-inducing (not "Interested in [Role]")
  - Good: "Your Postgres post + a question about the data team"
  - Good: "Ex-[Competitor] engineer — curious about [Company]'s scaling approach"
- **Body**: Hook → Credibility → Specific value → Soft ask
- **P.S.**: Optional — add a second hook or social proof

### Step 4 — Personalization Checklist

Before finalizing, verify the message:
- [ ] Mentions something specific to THIS person or company (not generic)
- [ ] Does NOT start with "I" or "My name is"
- [ ] Does NOT say "I'm very interested" or "I'd love to learn more"
- [ ] Is under the word limit
- [ ] Has ONE clear ask at the end
- [ ] Sounds like something a real person would say out loud
- [ ] Could not be sent word-for-word to a different person/company

### Step 5 — Variants and Follow-up

Generate:
1. **Primary message** — best version
2. **Shorter variant** — if they want something more punchy
3. **Follow-up message** — for if they don't respond after 5-7 days

The follow-up should:
- Acknowledge the previous message briefly
- Add new value (a new observation, article, or insight)
- Re-ask with an even easier CTA (e.g., "even a no works — just wanted to check")

## Tone Calibration

Adjust tone based on role level and company culture:

| Company Type | Tone |
|-------------|------|
| Startup / early-stage | Casual, direct, show curiosity about the product |
| Mid-size tech | Balanced, professional but not stiff |
| Enterprise / finance | More formal, lead with credentials |

| Role Level | Approach |
|-----------|---------|
| Recruiter | Keep it super short, include job title and link to your profile |
| Hiring Manager | Show you understand the team's work, not just the job description |
| VP/Director | Lead with company-level insight, not personal need |
| CEO/Founder | Reference their vision / public content, be extremely brief |

## Output

Deliver:
1. Primary outreach message (clearly labeled for copy-paste)
2. Short variant
3. Follow-up message
4. Subject line (if email)
5. One sentence on why this message should work
