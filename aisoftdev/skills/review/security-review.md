# Skill: Security Review

## Purpose
Audit code for security vulnerabilities before it ships, covering the OWASP Top 10 and common implementation errors specific to the project's stack.

## Inputs Required
- `target`: File path(s) or PR diff to review
- `context`: What the code does (e.g., "user authentication endpoints")
- `stack`: Language, framework, DB (check `memory/architecture.md`)

## OWASP Top 10 Checklist

### A01 — Broken Access Control
- [ ] Every route that returns or modifies user data checks that the requesting user owns or has permission to access that resource
- [ ] Admin-only routes are protected by role checks, not just authentication
- [ ] Directory traversal not possible via user-supplied file paths
- [ ] CORS policy is restrictive (not `*` in production)
- [ ] Sensitive operations require re-authentication or 2FA where appropriate

**Red flags to grep for:**
```
req.params.userId  (used without comparing to req.user.id)
req.query.file     (used in fs.readFile without sanitization)
```

### A02 — Cryptographic Failures
- [ ] Passwords hashed with bcrypt/argon2/scrypt (NOT md5, sha1, sha256 raw)
- [ ] Secrets not stored in source code, `.env` committed, or logs
- [ ] JWT secrets are cryptographically random and ≥ 256 bits
- [ ] Sensitive data encrypted at rest if stored in DB
- [ ] TLS enforced — no HTTP-only endpoints in production config

**Red flags:**
```
md5(password)
sha1(
crypto.createHash('sha256').update(password)
console.log(req.body)   (may log passwords)
JWT_SECRET = "secret"   (hardcoded)
```

### A03 — Injection
- [ ] All database queries use parameterized statements or ORM query builders — no string interpolation
- [ ] Shell commands do not include user input (or use `execFile` with args array, never `exec` with string)
- [ ] LDAP/XML/XPath queries not built from user input
- [ ] File paths built from user input are sanitized and constrained to allowed directories

**Red flags:**
```typescript
db.query(`SELECT * FROM users WHERE id = ${userId}`)   // ❌ SQL injection
exec(`convert ${filename} output.png`)                  // ❌ command injection
```

**Safe patterns:**
```typescript
db.query('SELECT * FROM users WHERE id = $1', [userId])  // ✅
execFile('convert', [filename, 'output.png'])             // ✅
```

### A04 — Insecure Design
- [ ] Rate limiting on authentication endpoints (login, register, password reset)
- [ ] Account enumeration not possible (login/forgot-password returns same response for existing vs. non-existing email)
- [ ] Password reset tokens expire and are single-use
- [ ] Brute-force protection on sensitive operations

### A05 — Security Misconfiguration
- [ ] Default credentials removed
- [ ] Debug mode and stack traces disabled in production
- [ ] Error responses do not reveal framework version, file paths, or SQL
- [ ] HTTP security headers present: `Helmet.js` or equivalent
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Strict-Transport-Security`
  - `Content-Security-Policy`

### A06 — Vulnerable Components
- [ ] `npm audit` / `pip audit` / `bundle audit` run and results reviewed
- [ ] No packages with critical/high CVEs without documented mitigation
- [ ] Lock file (`package-lock.json`, `poetry.lock`) committed and up to date

### A07 — Authentication Failures
- [ ] Passwords have minimum strength requirements (length, complexity)
- [ ] Tokens invalidated on logout (if using server-side sessions or token blocklist)
- [ ] JWT `exp` claim present and short-lived (≤ 1 hour for access tokens)
- [ ] Refresh token rotation implemented
- [ ] Multi-factor authentication available for sensitive accounts

### A08 — Software and Data Integrity
- [ ] Deserialization of untrusted data not performed (pickle, Java deserialization, etc.)
- [ ] Package integrity verified (subresource integrity for CDN assets)
- [ ] CI/CD pipeline protected from unauthorized changes

### A09 — Security Logging & Monitoring
- [ ] Failed authentication attempts logged with IP and timestamp
- [ ] Sensitive operations (password change, privilege escalation) logged
- [ ] Logs do NOT contain: passwords, tokens, PII beyond minimum necessary
- [ ] Logs stored separately from application (not only to stdout)

### A10 — Server-Side Request Forgery (SSRF)
- [ ] URLs provided by users are not fetched by the server without allowlist validation
- [ ] Internal metadata endpoints (169.254.169.254) blocked in outbound requests

## Frontend-Specific Checks
- [ ] User-generated content rendered with escaping — no `dangerouslySetInnerHTML` with user data
- [ ] `eval()` not used with any user-controlled data
- [ ] Sensitive data not stored in `localStorage` (use `httpOnly` cookies for tokens)
- [ ] Forms have CSRF protection if not using stateless JWT

## Output Format
```markdown
# Security Review: {target}
**Date:** {date}
**Reviewer:** QA Agent
**Severity Legend:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low | ✅ Pass

## Findings

### 🔴 [CRITICAL] SQL Injection in /api/users/search
**File:** src/routes/users.ts:47
**Issue:** User input interpolated directly into SQL query string
**Fix:** Use parameterized query: `db.query('... WHERE name = $1', [req.query.name])`

### 🟡 [MEDIUM] Password logged on registration failure
**File:** src/services/authService.ts:23
**Issue:** `console.error('Registration failed', data)` — `data` contains raw password
**Fix:** Log only non-sensitive fields: `console.error('Registration failed', { email: data.email })`

## Passed Checks
- ✅ All SQL queries use Prisma ORM (parameterized)
- ✅ Passwords hashed with bcrypt (cost factor 12)
- ✅ JWT expiry set to 15 minutes

## Dependency Audit
npm audit: 0 critical, 1 high (see details below)
...

## Verdict
🔴 FAIL — 1 critical finding must be resolved before release.
```

## Checklist Before Delivery
- [ ] All OWASP Top 10 categories checked
- [ ] Every finding includes file path, line number, and a specific fix
- [ ] Dependency audit run and results included
- [ ] Clear PASS or FAIL verdict stated
