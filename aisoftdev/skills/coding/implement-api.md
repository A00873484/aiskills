# Skill: Implement API

## Purpose
Design and implement a well-structured API endpoint (REST or GraphQL) following the project's conventions, with proper validation, error handling, and documentation.

## Inputs Required
- `endpoint`: HTTP method + path (e.g., `POST /api/v1/users`) or GraphQL mutation/query name
- `description`: What this endpoint does in plain English
- `request_schema`: Expected request body / query params (JSON Schema or TypeScript type)
- `response_schema`: Expected response shape
- `auth_required`: Whether authentication is required
- `framework`: Express, Fastify, NestJS, FastAPI, Hono, etc. (check `memory/architecture.md`)

## Process

### Step 1 — Design First
Before writing code, define:
1. Route path and HTTP method
2. Request validation schema (use Zod, Joi, Pydantic, or framework equivalent)
3. Response schema for success and all error cases
4. Auth/authorization requirements
5. Side effects (DB writes, events emitted, emails sent)

Write a brief design comment at the top of the route file.

### Step 2 — Implement the Route Handler
Structure every handler as:
```
validate input → check auth/authz → execute business logic → return response
```

**Template (TypeScript/Express example):**
```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { z } from 'zod';

const router = Router();

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  password: z.string().min(8),
});

router.post('/users', requireAuth, async (req: Request, res: Response, next: NextFunction) => {
  try {
    const body = CreateUserSchema.safeParse(req.body);
    if (!body.success) {
      return res.status(400).json({ error: 'Validation failed', details: body.error.flatten() });
    }

    const user = await userService.create(body.data);

    return res.status(201).json({ data: user });
  } catch (err) {
    next(err);
  }
});
```

### Step 3 — Implement the Service Layer
Business logic lives in a service, never in the route handler:
```typescript
// src/services/userService.ts
export async function create(data: CreateUserInput): Promise<User> {
  const existing = await db.user.findUnique({ where: { email: data.email } });
  if (existing) throw new ConflictError('Email already registered');

  const hashed = await bcrypt.hash(data.password, 12);
  return db.user.create({ data: { ...data, password: hashed } });
}
```

### Step 4 — Document the Endpoint
Add OpenAPI annotation (JSDoc or decorator depending on framework):
```typescript
/**
 * @openapi
 * /api/v1/users:
 *   post:
 *     summary: Create a new user
 *     requestBody:
 *       required: true
 *       content:
 *         application/json:
 *           schema:
 *             $ref: '#/components/schemas/CreateUser'
 *     responses:
 *       201:
 *         description: User created
 *       400:
 *         description: Validation error
 *       409:
 *         description: Email already exists
 */
```

### Step 5 — Wire Up
- Register the router in the main app file
- Add the route to the API index/barrel file
- Confirm no conflicting routes exist

## Error Response Standard
Always return errors in this shape:
```json
{
  "error": "Human-readable message",
  "code": "MACHINE_READABLE_CODE",
  "details": {}
}
```

## HTTP Status Code Guide
| Situation | Code |
|-----------|------|
| Created successfully | 201 |
| Updated/deleted successfully | 200 |
| Validation failure | 400 |
| Not authenticated | 401 |
| Not authorized | 403 |
| Resource not found | 404 |
| Duplicate / conflict | 409 |
| Unhandled server error | 500 |

## Checklist Before Delivery
- [ ] Input validated with schema library (not manual if/else)
- [ ] All error cases return appropriate status codes
- [ ] No business logic in the route handler
- [ ] Endpoint documented with OpenAPI annotation
- [ ] Route registered and reachable
- [ ] Corresponding tests written (see `skills/coding/write-tests.md`)
