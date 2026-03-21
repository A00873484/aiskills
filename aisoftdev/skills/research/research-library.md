# Skill: Research Library

## Purpose
Evaluate one or more libraries/packages to determine the best fit for a specific need, producing a recommendation backed by evidence.

## Inputs Required
- `need`: What problem needs to be solved (e.g., "schema validation for API inputs")
- `candidates`: Specific libraries to evaluate (optional — if empty, discover candidates first)
- `constraints`: Must-haves (e.g., "TypeScript support", "tree-shakeable", "works in Node 18+", "MIT license")
- `context`: Current stack from `memory/architecture.md`

## Process

### Step 1 — Discover Candidates (if not provided)
Search for the top 3–5 libraries solving the stated need. Sources to check:
- npm/PyPI search for keywords
- "awesome-{technology}" GitHub lists
- State of JS / State of Python surveys
- Recent comparison articles (check publish date — prefer < 2 years old)

### Step 2 — Evaluate Each Candidate
Score each library across these dimensions:

| Dimension | What to Check |
|-----------|--------------|
| **Adoption** | Weekly downloads, GitHub stars, used by major projects |
| **Maintenance** | Last commit date, open issues trend, response time to PRs |
| **API quality** | Is the API ergonomic? Does it fit the team's patterns? |
| **TypeScript** | First-class types, or `@types/` package, or none |
| **Bundle size** | Check bundlephobia.com for frontend libraries |
| **License** | MIT/Apache preferred; GPL requires legal review |
| **Security** | Run `npm audit` or check known CVEs; check Snyk advisors |
| **Documentation** | Is the docs site comprehensive? Are examples practical? |
| **Ecosystem fit** | Integrates well with our existing stack? |

### Step 3 — Comparison Table
Produce a structured comparison:

```markdown
## Library Comparison: Schema Validation

| | Zod | Joi | Yup |
|---|---|---|---|
| Weekly downloads | 12M | 8M | 6M |
| TypeScript | Native | via @types | via @types |
| Bundle size | 12kb | 25kb | 18kb |
| Last commit | 3 days ago | 2 weeks ago | 1 month ago |
| License | MIT | MIT | MIT |
| API style | Chainable, inferrable | Chainable | Chainable |
| Runtime parsing | ✅ | ✅ | ✅ |
| Static inference | ✅ Native | ❌ | ❌ |
```

### Step 4 — Recommendation
State a clear recommendation with rationale:

```markdown
## Recommendation: Zod

**Choose Zod** because:
1. TypeScript-first — types are inferred from the schema definition, eliminating duplication
2. Highest adoption and active maintenance
3. Smallest bundle footprint
4. API integrates naturally with tRPC and React Hook Form (both already in our stack)

**Do not use Joi** — no native TypeScript type inference.
**Do not use Yup** — lower maintenance activity; Zod has superseded it in the TS ecosystem.
```

### Step 5 — Integration Notes
Provide a minimal usage example in the project's language and style:
```typescript
// Install: npm install zod
import { z } from 'zod';

const UserSchema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150),
});

type User = z.infer<typeof UserSchema>; // Free TypeScript type
const result = UserSchema.safeParse(req.body);
```

### Step 6 — Record the Decision
If a library is selected, add it to `memory/decisions.md`:
```markdown
## [Date] Schema validation library: Zod
- Chosen over: Joi, Yup
- Reason: Native TypeScript inference, active maintenance, ecosystem fit
- Version locked at: 3.x
```

## Output Format
```markdown
# Library Research: {need}

## Candidates Evaluated
{list}

## Comparison Table
{table}

## Recommendation
{library} — {one-sentence justification}

## Integration Example
{code snippet}

## Decision to Record
{decision entry for memory/decisions.md}
```

## Checklist Before Delivery
- [ ] At least 3 candidates compared
- [ ] Comparison table includes adoption, maintenance, and license
- [ ] Clear recommendation with justification
- [ ] Integration example is runnable
- [ ] Decision ready to be recorded in `memory/decisions.md`
