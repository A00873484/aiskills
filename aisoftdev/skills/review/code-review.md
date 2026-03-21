# Skill: Code Review

## Purpose
Review code for correctness, clarity, maintainability, and adherence to project conventions — as a thorough, constructive senior engineer would.

## Inputs Required
- `target`: File path(s) or diff to review
- `context`: What the code is supposed to do
- `standards`: Link to project conventions (check `memory/architecture.md`)

## Review Dimensions

### 1. Correctness
Does the code actually do what it's supposed to?
- [ ] Logic matches the requirement specification
- [ ] Edge cases handled: null/undefined, empty collections, zero, negative numbers
- [ ] Error conditions handled explicitly — no silent failures
- [ ] Async errors caught (no unhandled promise rejections)
- [ ] Race conditions considered for concurrent operations
- [ ] Off-by-one errors in loops and pagination

### 2. Readability
Can a new engineer understand this in 5 minutes?
- [ ] Variable and function names clearly express intent
- [ ] No abbreviations except universally understood ones (id, url, http)
- [ ] Functions do one thing and are ≤ 40 lines
- [ ] Complex logic has a brief comment explaining *why*, not *what*
- [ ] Magic numbers replaced with named constants
- [ ] Nested ternaries avoided (use early return or if/else)

### 3. Maintainability
Will this be easy to change in 6 months?
- [ ] No duplication — shared logic is extracted
- [ ] Dependencies are injected (not created inline) for testability
- [ ] No hardcoded values that will need to change (URLs, timeouts, limits)
- [ ] Code follows the single responsibility principle
- [ ] Public API is stable and minimal

### 4. Performance
Is it efficient enough for production load?
- [ ] No N+1 queries (loop calling DB each iteration)
- [ ] Expensive operations cached where appropriate
- [ ] Large payloads paginated, not loaded entirely into memory
- [ ] No blocking operations on the main thread (Node.js)
- [ ] Database queries use indexes for filtered/sorted columns

### 5. Convention Adherence
Does it match the project's patterns?
- [ ] Follows folder/file naming convention from `memory/architecture.md`
- [ ] Uses established libraries (no new dependencies without Director approval)
- [ ] Error handling follows project's error class hierarchy
- [ ] Logging uses the project's structured logger (not raw `console.log`)
- [ ] Types used consistently — no `any` without justification

### 6. Tests
Is the code adequately verified?
- [ ] Unit tests cover all branches
- [ ] Integration tests cover the primary use case
- [ ] Test names describe behavior: `it('returns 404 when user not found')`
- [ ] Tests are independent — no shared mutable state between them

## Severity Levels
| Level | Meaning | Action |
|-------|---------|--------|
| **Blocker** | Bug, security issue, or broken contract | Must fix before merge |
| **Major** | Significant readability or maintainability problem | Should fix before merge |
| **Minor** | Style, naming, or small improvement | Fix if convenient |
| **Nit** | Cosmetic | Optional |

## Output Format

```markdown
# Code Review: {target}
**Reviewer:** QA Agent / {requesting agent}
**Date:** {date}

## Summary
{2-3 sentences on overall quality and the main concerns}

## Findings

### 🔴 [Blocker] Unhandled promise rejection in createOrder
**File:** src/services/orderService.ts:88
**Issue:** `await paymentGateway.charge(amount)` is not wrapped in try/catch.
If the payment gateway throws, the error propagates uncaught and the order
is created without payment.
**Fix:**
\`\`\`typescript
try {
  await paymentGateway.charge(amount);
} catch (err) {
  throw new PaymentError('Charge failed', { cause: err });
}
\`\`\`

### 🟠 [Major] N+1 query in getOrdersWithItems
**File:** src/services/orderService.ts:120
**Issue:** For each order, a separate DB query fetches line items. With 100 orders,
this executes 101 queries.
**Fix:** Use `include: { items: true }` in the initial Prisma query.

### 🟡 [Minor] Magic number 86400
**File:** src/auth/tokenService.ts:14
**Issue:** `expiresIn: 86400` — seconds in a day. Not obvious to the reader.
**Fix:** `const ONE_DAY_SECONDS = 60 * 60 * 24;`

### ✅ Positives
- Clean separation of route handler and service layer
- Zod validation is thorough and covers nested objects
- Tests are well-structured with clear names

## Verdict
🟠 Approve with changes — fix blocker and N+1 issue before merging.

## Checklist
- [ ] Blocker resolved
- [ ] Major issues addressed
- [ ] Re-review requested? Yes / No
```

## Review Principles
- Be specific — "this is confusing" is useless; explain exactly what's confusing and why
- Propose solutions, not just problems
- Acknowledge what's done well — a review with only negatives is demoralizing and less useful
- Distinguish opinion from fact — prefix opinions with "I'd prefer..." or "Consider..."
- Focus on the code, never the author
