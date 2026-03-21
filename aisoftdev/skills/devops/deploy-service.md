# Skill: Deploy Service

## Purpose
Deploy a containerized service to the target environment using a safe, repeatable, zero-downtime deployment procedure.

## Inputs Required
- `service`: Service name (matches docker-compose service or K8s deployment name)
- `environment`: `staging` | `production`
- `artifact`: Docker image tag or git SHA to deploy (e.g., `api:a1b2c3d`)
- `deployment_target`: `docker-compose` | `kubernetes` | `aws-ecs` | `railway` | `fly.io`
- `pre_deploy_checks`: List of checks that must pass before deploying

## Pre-Deploy Gates (MUST pass before proceeding)
- [ ] All tests passing in CI for the target commit
- [ ] Docker image built and pushed to registry
- [ ] `skills/review/security-review.md` completed with no critical findings
- [ ] Staging deploy succeeded before production
- [ ] Database migrations reviewed (destructive migrations require manual approval)
- [ ] Rollback plan documented

**If any gate fails: STOP. Do not deploy. File a blocker task.**

## Deployment Procedures

### Docker Compose (self-hosted)

```bash
# 1. Pull latest image
docker pull registry.example.com/{service}:{tag}

# 2. Backup current state
docker inspect {service}_api_1 > /tmp/pre-deploy-snapshot.json

# 3. Zero-downtime rolling update
docker-compose up -d --no-deps --scale api=2 api
sleep 15  # wait for new containers to be healthy
docker-compose up -d --no-deps --scale api=1 api

# 4. Verify health
docker-compose ps
curl -f http://localhost:{port}/health

# 5. Clean up old images
docker image prune -f
```

### Kubernetes

```bash
# 1. Set image (triggers rolling update)
kubectl set image deployment/{service} \
  {container}=registry.example.com/{service}:{tag} \
  -n {namespace}

# 2. Monitor rollout
kubectl rollout status deployment/{service} -n {namespace} --timeout=5m

# 3. Verify pods are healthy
kubectl get pods -n {namespace} -l app={service}

# 4. Check recent logs
kubectl logs -n {namespace} -l app={service} --since=5m --tail=100
```

### Fly.io

```bash
fly deploy --image registry.example.com/{service}:{tag} --app {app-name}
fly status --app {app-name}
fly logs --app {app-name}
```

### Railway

```bash
railway up --service {service} --environment {environment}
```

## Database Migration Procedure
Run migrations **before** deploying new code (backward-compatible migrations only):

```bash
# Docker Compose
docker run --rm \
  --env-file .env.{environment} \
  registry.example.com/{service}:{tag} \
  npm run db:migrate

# Kubernetes
kubectl run migration --rm --restart=Never \
  --image=registry.example.com/{service}:{tag} \
  -n {namespace} \
  -- npm run db:migrate
```

**Destructive migrations** (dropping columns, renaming tables) require:
1. Three-phase deploy: (1) deploy code that handles both old/new schema, (2) run migration, (3) deploy code that uses new schema only
2. Human approval before running
3. Database backup verified within last hour

## Post-Deploy Verification
Run within 5 minutes of deployment:

```bash
# Health check
curl -f https://{domain}/health

# Smoke test critical endpoints
curl -X POST https://{domain}/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"smoke@test.com","password":"smoketest"}'

# Check error rates (if observability is set up)
# Verify in dashboard: error rate < 1%, p99 latency < 2s

# Check logs for unexpected errors
# (kubectl logs, docker-compose logs, or log aggregation tool)
```

## Rollback Procedure
If post-deploy verification fails within 10 minutes:

```bash
# Docker Compose
docker-compose up -d --no-deps {service}  # reverts to previous image in compose file

# Kubernetes
kubectl rollout undo deployment/{service} -n {namespace}
kubectl rollout status deployment/{service} -n {namespace}

# Fly.io
fly releases -a {app-name}
fly deploy --image registry.example.com/{service}:{previous-tag} --app {app-name}
```

After rollback: file a `BLOCKED` task with logs, and notify the Director.

## Environment Variables Management
- Never pass secrets as CLI arguments (visible in `ps aux`)
- Use environment-specific `.env` files (not committed to git) or secret managers
- For Kubernetes: use `Secrets`, not `ConfigMaps`, for sensitive values
- Verify all required env vars are present before deploying:

```bash
# Check required vars are set
required_vars=(DATABASE_URL JWT_SECRET REDIS_URL)
for var in "${required_vars[@]}"; do
  [[ -z "${!var}" ]] && echo "ERROR: $var is not set" && exit 1
done
```

## Output Format
```markdown
# Deployment Report: {service} → {environment}
**Date:** {timestamp}
**Image:** {tag}
**Deployed by:** Backend Agent / DevOps Skill
**Target:** {deployment_target}

## Pre-Deploy Checks
- ✅ CI passing
- ✅ Security review: PASS
- ✅ Staging verified

## Deployment Steps
1. ✅ Image pulled: registry.example.com/api:a1b2c3d
2. ✅ Migration run: 1 migration applied
3. ✅ Rolling update complete: 2/2 replicas healthy
4. ✅ Health check: HTTP 200

## Post-Deploy Verification
- ✅ /health: 200 OK
- ✅ Login smoke test: 200 OK
- ✅ Error rate: 0.02% (baseline: 0.01%)
- ✅ p99 latency: 180ms (baseline: 165ms)

## Status: SUCCESS
Rollback available: kubectl rollout undo deployment/api -n production
```

## Checklist Before Delivery
- [ ] All pre-deploy gates passed
- [ ] Migration (if any) completed successfully
- [ ] Post-deploy verification passed
- [ ] Rollback command documented in report
- [ ] Deployment report written
