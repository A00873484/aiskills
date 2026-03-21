# Architecture

This file is the single source of truth for the project's technical architecture.
All agents must read this before starting work. The Director updates it as decisions are made.

---

## Project Overview
**Name:** {project-name}
**Description:** {one-paragraph description}
**Status:** {Planning | In Development | Production}
**Last updated:** {date}

---

## Stack

### Backend
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Runtime | Node.js | 20.x LTS | |
| Framework | — | — | To be decided |
| Language | TypeScript | 5.x | Strict mode enabled |
| Validation | — | — | To be decided |
| ORM / DB client | — | — | To be decided |
| Auth | — | — | To be decided |
| Testing | Jest + Supertest | — | |

### Frontend
| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| Framework | — | — | To be decided |
| Language | TypeScript | 5.x | |
| Styling | — | — | To be decided |
| State | — | — | To be decided |
| Data fetching | — | — | To be decided |
| Testing | Vitest + Testing Library | — | |

### Infrastructure
| Concern | Technology | Notes |
|---------|-----------|-------|
| Database | — | To be decided |
| Cache | — | To be decided |
| Container | Docker + docker-compose | |
| CI/CD | — | To be decided |
| Hosting | — | To be decided |
| Secrets | .env (local), — (production) | |

---

## Repository Structure
```
/
├── src/
│   ├── routes/         # HTTP route handlers (thin — no business logic)
│   ├── services/       # Business logic layer
│   ├── models/         # DB models / ORM schemas
│   ├── middleware/     # Express/Fastify middleware
│   ├── lib/            # Shared utilities
│   └── types/          # Shared TypeScript types (also used by frontend)
├── tests/
│   ├── unit/
│   └── integration/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/
│   │   ├── pages/
│   │   └── lib/
│   └── tests/
├── migrations/         # Database migration files
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

---

## API Design Conventions
- All routes prefixed with `/api/v{n}/`
- Authentication via Bearer JWT in `Authorization` header
- Responses always JSON with shape `{ data: T }` (success) or `{ error: string, code: string }` (error)
- Pagination: `?page=1&limit=20`, response includes `{ data: T[], meta: { total, page, limit } }`
- Dates in ISO 8601 format (UTC)
- IDs as UUIDs (v4)

---

## Shared Type Contract
Types shared between backend and frontend live in `src/types/`.
Frontend imports from this path. Neither side duplicates type definitions.

---

## Environment Variables
| Variable | Used By | Description |
|----------|---------|-------------|
| `DATABASE_URL` | Backend | Full connection string |
| `JWT_SECRET` | Backend | HS256 signing key (min 32 chars) |
| `JWT_REFRESH_SECRET` | Backend | Refresh token signing key |
| `PORT` | Backend | HTTP server port (default 3000) |
| `NODE_ENV` | Both | `development` \| `test` \| `production` |
| `VITE_API_URL` | Frontend | Base URL for API calls |

Add new variables here when introduced. Include in `.env.example` with placeholder value.

---

## Coding Conventions
- **Naming:** camelCase for variables/functions, PascalCase for types/classes, kebab-case for files
- **Errors:** Throw custom error classes extending `AppError`. Never throw raw `new Error()` in services.
- **Logging:** Use the project logger (structured JSON). Never use `console.log` in production code.
- **No `any`:** TypeScript `any` requires a comment explaining why it's necessary.
- **Imports:** Absolute imports from `src/` (configured via `tsconfig.json` paths). No `../../..` chains.

---

## Service Boundaries
*(Fill in as services are designed)*

```
[Client] ──HTTP──► [API Gateway / Load Balancer]
                          │
              ┌───────────┴────────────┐
              ▼                        ▼
         [API Service]          [Worker Service]
              │                        │
         [Database]              [Message Queue]
```
