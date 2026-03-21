# Skill: Refactor Code

## Purpose
Improve the internal quality of existing code — readability, maintainability, testability, and performance — without changing observable behavior.

## Inputs Required
- `target`: File path(s) or module to refactor
- `goal`: What problem the refactor solves (e.g., "reduce duplication", "improve readability", "extract reusable logic", "improve performance")
- `constraints`: What must NOT change (e.g., "public API surface must remain identical", "no new dependencies")

## Principle: Never Break the Contract
A refactor must:
1. Produce identical outputs for all inputs the old code handled
2. Not change public function signatures unless explicitly requested
3. Pass all existing tests after the change
4. Not introduce new dependencies without Director approval

## Process

### Step 1 — Understand Before Changing
Read the target file(s) completely. Answer:
- What does this code do?
- What are the public interfaces (exports, API routes, component props)?
- Are there existing tests? Run them before touching anything.
- What are the pain points? (duplication, long functions, unclear names, deep nesting)

### Step 2 — Identify Refactor Type

| Smell | Refactor Technique |
|-------|-------------------|
| Function > 40 lines | Extract sub-functions |
| Duplicated logic (≥3 occurrences) | Extract shared utility |
| Deep nesting (>3 levels) | Early return / guard clauses |
| Magic numbers/strings | Named constants |
| Mixed concerns in one file | Separate into modules |
| Hard to test (external deps inlined) | Dependency injection |
| Complex conditionals | Replace with strategy/map pattern |
| Mutable shared state | Encapsulate or eliminate |

### Step 3 — Refactor in Small, Safe Steps
Each step should be independently committable:
1. Extract without changing behavior
2. Rename for clarity
3. Simplify logic
4. Remove dead code last (after confirming via search)

**Example: Extract function**
```typescript
// Before
async function processOrder(order: Order) {
  // 20 lines of tax calculation
  const taxRate = order.region === 'EU' ? 0.2 : order.region === 'CA' ? 0.13 : 0.1;
  const tax = order.subtotal * taxRate;
  // ...more logic
}

// After
function getTaxRate(region: string): number {
  const rates: Record<string, number> = { EU: 0.2, CA: 0.13 };
  return rates[region] ?? 0.1;
}

async function processOrder(order: Order) {
  const tax = order.subtotal * getTaxRate(order.region);
  // ...
}
```

**Example: Guard clauses over nesting**
```typescript
// Before
function getDiscount(user: User) {
  if (user.active) {
    if (user.premium) {
      if (user.loyaltyYears > 5) {
        return 0.3;
      }
      return 0.2;
    }
    return 0.1;
  }
  return 0;
}

// After
function getDiscount(user: User): number {
  if (!user.active) return 0;
  if (!user.premium) return 0.1;
  if (user.loyaltyYears > 5) return 0.3;
  return 0.2;
}
```

### Step 4 — Verify
- Run the full test suite — all tests must pass
- If tests fail: the refactor broke behavior. Revert and rethink.
- If no tests exist: write characterization tests first, then refactor

### Step 5 — Document Changes
Write a brief summary of:
- What was changed and why
- Any patterns introduced that others should follow
- Anything that was intentionally left unchanged and why

## Common Pitfalls to Avoid
- Do not refactor and add features in the same change
- Do not rename public symbols without searching the entire codebase for usages
- Do not remove code that "looks unused" without running a dead code analysis
- Do not over-abstract — one extra function is better than a clever framework
- Do not change error messages that may be user-facing or tested

## Checklist Before Delivery
- [ ] All existing tests pass unchanged
- [ ] No public API surface changed (or change is intentional and approved)
- [ ] No new external dependencies added
- [ ] Code is simpler and/or shorter than before
- [ ] No behavior changes (verified by tests)
- [ ] Changes summarized in output
