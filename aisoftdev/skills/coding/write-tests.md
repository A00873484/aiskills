# Skill: Write Tests

## Purpose
Write a comprehensive, maintainable test suite for a given piece of code — covering happy paths, edge cases, and failure modes.

## Inputs Required
- `target`: File path or module to test
- `test_type`: `unit` | `integration` | `e2e` | `component`
- `framework`: Jest, Vitest, Pytest, Playwright, Cypress (check `memory/architecture.md`)
- `coverage_goal`: Minimum coverage percentage (default: 85%)

## Test Types

### Unit Tests
Test a single function or class in isolation. Mock all external dependencies.
- Target: services, utilities, business logic, pure functions
- Speed: milliseconds
- Mock: database, HTTP calls, filesystem, timers

### Integration Tests
Test multiple components working together. Use a real (test) database.
- Target: API route handlers, service + DB layer combos
- Speed: seconds
- Mock: third-party external APIs only

### Component Tests
Test UI components in isolation with simulated user interactions.
- Target: React/Vue components
- Tools: React Testing Library, Vue Test Utils
- Focus: what the user sees and can do, not implementation details

### E2E Tests
Test full user flows through the real application.
- Target: critical user journeys (sign up, checkout, core feature)
- Tools: Playwright or Cypress
- Run: CI only (slow, use sparingly)

## Process

### Step 1 — Analyze the Target
Read the target file. Identify:
- All exported functions/components/classes
- All branches (if/else, switch, ternary)
- All error conditions (throws, rejects, error responses)
- All external dependencies to mock

### Step 2 — Write Test Cases Using the AAA Pattern
**Arrange** — set up inputs, mocks, and state
**Act** — call the function under test
**Assert** — verify the output or side effect

```typescript
describe('userService.create', () => {
  // Happy path
  it('creates a user and returns it without the password field', async () => {
    // Arrange
    const input = { email: 'test@example.com', name: 'Ada', password: 'secret123' };
    mockDb.user.create.mockResolvedValue({ id: '1', email: input.email, name: input.name });

    // Act
    const result = await userService.create(input);

    // Assert
    expect(result).toEqual({ id: '1', email: input.email, name: input.name });
    expect(result).not.toHaveProperty('password');
  });

  // Error path
  it('throws ConflictError when email already exists', async () => {
    mockDb.user.findUnique.mockResolvedValue({ id: 'existing' });

    await expect(userService.create({ email: 'dupe@example.com', name: 'X', password: 'pass' }))
      .rejects.toThrow('Email already registered');
  });

  // Edge case
  it('trims whitespace from email before saving', async () => {
    const input = { email: '  padded@example.com  ', name: 'X', password: 'pass' };
    await userService.create(input);
    expect(mockDb.user.create).toHaveBeenCalledWith(
      expect.objectContaining({ data: expect.objectContaining({ email: 'padded@example.com' }) })
    );
  });
});
```

### Step 3 — Cover These Cases for Every Function
| Category | Examples |
|----------|---------|
| Happy path | Valid input, expected output |
| Invalid input | Wrong type, missing required field, out-of-range value |
| Boundary values | Empty string, zero, max int, null, undefined |
| Error propagation | Dependency throws — does caller handle or rethrow correctly? |
| Side effects | Was the DB called with correct args? Was an event emitted? |
| Auth/authz | Unauthenticated request rejected? Unauthorized user blocked? |

### Step 4 — Mocking Strategy

**TypeScript/Jest:**
```typescript
jest.mock('../db', () => ({
  user: {
    findUnique: jest.fn(),
    create: jest.fn(),
  },
}));
const mockDb = jest.mocked(db);

beforeEach(() => {
  jest.clearAllMocks();
});
```

**Python/pytest:**
```python
@pytest.fixture
def mock_db(mocker):
    return mocker.patch('app.services.user_service.db')

def test_create_user(mock_db):
    mock_db.user.find_unique.return_value = None
    # ...
```

### Step 5 — API Integration Test Template
```typescript
describe('POST /api/v1/users', () => {
  it('returns 201 and the created user', async () => {
    const res = await request(app)
      .post('/api/v1/users')
      .send({ email: 'new@example.com', name: 'New User', password: 'strongpass1' });

    expect(res.status).toBe(201);
    expect(res.body.data).toMatchObject({ email: 'new@example.com' });
    expect(res.body.data).not.toHaveProperty('password');
  });

  it('returns 400 for invalid email', async () => {
    const res = await request(app)
      .post('/api/v1/users')
      .send({ email: 'not-an-email', name: 'X', password: 'pass' });

    expect(res.status).toBe(400);
    expect(res.body).toHaveProperty('error');
  });
});
```

## Naming Convention
```
<unit>.<test type>.ts   →   userService.unit.test.ts
<route>.integration.test.ts
<component>.component.test.tsx
<flow>.e2e.spec.ts
```

## Coverage Check
After writing tests, run coverage and identify gaps:
```bash
npx jest --coverage
# or
npx vitest run --coverage
```
Any function/branch below target coverage must have additional tests written.

## Checklist Before Delivery
- [ ] Every exported function has at least one test
- [ ] All error branches tested
- [ ] Mocks reset between tests (`beforeEach(() => jest.clearAllMocks())`)
- [ ] No test depends on another test's state
- [ ] Tests are readable — a reviewer can understand intent without reading source
- [ ] Coverage meets or exceeds target
- [ ] Tests pass: `0 failed`
