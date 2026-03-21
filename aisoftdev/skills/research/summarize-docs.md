# Skill: Summarize Docs

## Purpose
Read official documentation, RFCs, changelogs, or technical specs and distill the essential information an engineer needs to use or integrate the subject effectively — without reading the full source.

## Inputs Required
- `source`: URL, file path, or name of the documentation to summarize
- `goal`: What the engineer needs to accomplish (e.g., "set up authentication with Clerk", "migrate from v3 to v4")
- `audience`: Which agent will consume this summary (`backend`, `frontend`, `qa`, `director`)
- `depth`: `overview` | `integration-guide` | `deep-dive`

## Depth Levels

### overview
A 1-page summary covering:
- What is it and what problem does it solve
- Core concepts and mental model
- When to use it vs. alternatives
- 3 key gotchas

### integration-guide
A practical how-to covering:
- Installation and setup
- The 3–5 most common use cases with code examples
- Configuration options that matter
- Common errors and how to fix them

### deep-dive
Full technical reference covering:
- Complete API surface relevant to our use case
- Internals that affect our usage (e.g., caching behavior, connection pooling)
- Performance characteristics
- Edge cases and known limitations

## Process

### Step 1 — Fetch and Scan
Read the documentation source. Do a first pass to identify:
- Table of contents / structure
- Which sections are relevant to the stated goal
- Version of the software being documented

### Step 2 — Extract Key Concepts
Identify and define the 5–10 core concepts a reader must understand.
Explain each in 1–2 sentences, in plain English.

Example for Prisma docs:
```
- Schema: Declarative database model definition in `schema.prisma`
- Client: Auto-generated, type-safe query builder (`@prisma/client`)
- Migration: Version-controlled schema change applied to the DB via `prisma migrate`
- Relation: How models reference each other (one-to-many, many-to-many)
```

### Step 3 — Extract Practical Examples
Pull the most instructive code examples. Annotate confusing parts.

### Step 4 — Highlight Gotchas
List any non-obvious behavior, common mistakes, or version-specific issues:
```
⚠️  Gotcha: `findUnique` returns null (not throws) when record not found.
⚠️  Gotcha: `prisma.$transaction` does not support cross-datasource operations.
⚠️  Gotcha: In v5, `rejectOnNotFound` was removed — use `findUniqueOrThrow` instead.
```

### Step 5 — Format the Summary

```markdown
# [Library/Tool Name] — {depth} Summary
**Version:** x.y.z
**Source:** {url or file}
**Goal:** {what the consumer wants to do}
**Audience:** {backend | frontend | qa}

## What It Is
{1 paragraph}

## Core Concepts
- **Concept**: Definition
- ...

## Quick Start
{minimal working code to get running}

## Common Patterns
### Pattern 1: {name}
{code example + explanation}

### Pattern 2: {name}
{code example + explanation}

## Configuration Reference
| Option | Type | Default | Description |
|--------|------|---------|-------------|
| ...    | ...  | ...     | ...         |

## Gotchas & Warnings
- ⚠️  {warning 1}
- ⚠️  {warning 2}

## Relevant Links
- {link to specific page that's most useful}
```

## Output Quality Standards
- Code examples must be minimal and functional — no extra boilerplate
- Avoid copying large blocks verbatim — paraphrase and annotate
- Flag anything that differs between the documented version and what's in `memory/architecture.md`
- If the docs are outdated (> 1 major version behind), flag this prominently

## Checklist Before Delivery
- [ ] Version of the library clearly stated
- [ ] Core concepts explained in plain English
- [ ] At least 2 working code examples
- [ ] Gotchas section present
- [ ] Summary is ≤ 2 pages for `overview`, ≤ 5 pages for `integration-guide`
- [ ] Targeted to the correct audience agent
