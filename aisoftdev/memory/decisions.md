# Decision Log

This file records all significant technical decisions made during the project.
Each entry includes the decision, the alternatives considered, and the rationale.
The Director writes here. All agents read here before choosing tools or libraries.

**Format:**
```
## [YYYY-MM-DD] Decision title
- **Decision:** What was chosen
- **Alternatives considered:** What else was evaluated
- **Rationale:** Why this choice was made
- **Constraints:** Any limitations this decision introduces
- **Revisit if:** Conditions under which this decision should be reconsidered
```

---

## Decision Index
*(Updated by Director as entries are added)*

| # | Date | Topic | Decision |
|---|------|-------|----------|
| 1 | — | — | — |

---

## Entries

### [Template] Decision Title
- **Decision:** {what was chosen}
- **Alternatives considered:** {option A — reason rejected}, {option B — reason rejected}
- **Rationale:** {why this was the best fit given our constraints}
- **Constraints introduced:** {what becomes harder or impossible with this choice}
- **Revisit if:** {e.g., "team grows beyond 10 engineers", "we need real-time features", "PostgreSQL becomes a bottleneck"}

---

## Open Questions
*(Decisions that haven't been made yet — Director fills these in during planning)*

| Question | Owner | Target Decision Date |
|----------|-------|---------------------|
| Which backend framework? (Express, Fastify, NestJS, Hono) | Director | — |
| SQL or NoSQL database? | Director | — |
| Monorepo or separate repos for frontend/backend? | Director | — |
| Authentication strategy (JWT, session, magic link, OAuth)? | Director | — |
| Frontend framework (React, Vue, Svelte)? | Director | — |
| Deployment target (self-hosted, Fly.io, Railway, AWS)? | Director | — |
| Real-time requirements (WebSockets, SSE, polling)? | Director | — |

---

## Principles (Non-Negotiable)
These are standing decisions that apply to all work, not up for re-evaluation per feature:

1. **Security first** — Every task goes through `skills/review/security-review.md` before shipping
2. **Tests required** — No feature ships without tests meeting coverage targets
3. **No secrets in code** — Credentials always via environment variables
4. **Reversibility** — Prefer decisions that are easy to undo or evolve
5. **Simplicity** — Choose the simpler option when capability is equal
