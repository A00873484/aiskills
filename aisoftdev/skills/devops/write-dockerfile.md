# Skill: Write Dockerfile

## Purpose
Produce a production-grade, secure, minimal Dockerfile (and docker-compose.yml when needed) for a given service.

## Inputs Required
- `service`: Name of the service (e.g., `api`, `worker`, `frontend`)
- `runtime`: `node`, `python`, `go`, `rust`, `java`, etc.
- `runtime_version`: e.g., `20`, `3.12`, `1.21`
- `entrypoint`: Command to start the service (e.g., `node dist/server.js`)
- `port`: Port the service listens on
- `env_vars`: List of required environment variables (names only — no values)
- `has_build_step`: Whether there's a compile/build step (TypeScript, React, etc.)

## Principles
1. **Minimal image** — use the smallest viable base image
2. **Non-root user** — never run as root in production
3. **Layer caching** — copy dependency manifests before source code
4. **Multi-stage builds** — separate build and runtime stages when there's a build step
5. **No secrets in layers** — env vars only; never bake credentials into the image
6. **Explicit versions** — pin base image tags; never use `latest`

## Base Image Selection

| Runtime | Development | Production |
|---------|-------------|------------|
| Node.js | `node:20-slim` | `node:20-alpine` |
| Python | `python:3.12-slim` | `python:3.12-alpine` or `gcr.io/distroless/python3` |
| Go | `golang:1.21-alpine` (build) | `gcr.io/distroless/static` or `alpine:3.19` (runtime) |
| Java | `eclipse-temurin:21-jdk` (build) | `eclipse-temurin:21-jre-alpine` (runtime) |

## Node.js Multi-Stage Template

```dockerfile
# ─── Build Stage ───────────────────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (cached layer)
COPY package*.json ./
RUN npm ci --ignore-scripts

# Copy source and build
COPY tsconfig.json ./
COPY src/ ./src/
RUN npm run build

# Prune dev dependencies
RUN npm ci --omit=dev --ignore-scripts

# ─── Runtime Stage ─────────────────────────────────────────────────────────────
FROM node:20-alpine AS runtime

# Security: create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

# Copy only production artifacts
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules
COPY --from=builder --chown=appuser:appgroup /app/dist ./dist
COPY --chown=appuser:appgroup package.json ./

# Drop to non-root
USER appuser

# Document port (does not publish — use -p at runtime or docker-compose)
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:3000/health || exit 1

CMD ["node", "dist/server.js"]
```

## Python Multi-Stage Template

```dockerfile
# ─── Build Stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

RUN pip install --no-cache-dir poetry==1.7.1
COPY pyproject.toml poetry.lock ./
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# ─── Runtime Stage ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

RUN groupadd -r appgroup && useradd -r -g appgroup appuser

WORKDIR /app

COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=appuser:appgroup src/ ./src/

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8000/health || exit 1
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## .dockerignore
Always include a `.dockerignore` to minimize build context:
```
node_modules/
dist/
.git/
.env
.env.*
*.log
coverage/
.nyc_output/
__pycache__/
*.pyc
.pytest_cache/
README.md
docker-compose*.yml
```

## docker-compose.yml Template
```yaml
version: '3.9'

services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: runtime
    image: {service-name}:${TAG:-latest}
    restart: unless-stopped
    ports:
      - "${PORT:-3000}:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=${DATABASE_URL}
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## Security Checklist
- [ ] Non-root user created and used
- [ ] Base image pinned to specific version (not `latest`)
- [ ] `.dockerignore` excludes `.env`, secrets, and dev artifacts
- [ ] No secrets passed as `ARG` or `ENV` in Dockerfile (use runtime env vars)
- [ ] Multi-stage build used when build step exists
- [ ] `HEALTHCHECK` defined
- [ ] `--no-cache-dir` used for pip; `--ignore-scripts` for npm
- [ ] Image size verified reasonable (`docker build` and check size)

## Checklist Before Delivery
- [ ] Dockerfile linted (`hadolint Dockerfile` — zero errors or documented exceptions)
- [ ] Image builds successfully: `docker build -t test .`
- [ ] Container starts and health check passes: `docker run -p 3000:3000 test`
- [ ] Non-root user confirmed: `docker run test whoami` returns non-root
- [ ] `.dockerignore` included
