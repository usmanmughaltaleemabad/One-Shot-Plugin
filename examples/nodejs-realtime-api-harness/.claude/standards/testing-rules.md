---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Node.js Testing Rules

## Use Jest + supertest

```typescript
import request from 'supertest';
import app from '../app';

describe('POST /subscriptions', () => {
  it('returns 201 with valid body', async () => {
    const res = await request(app)
      .post('/subscriptions')
      .send({ userId: '1', plan: 'pro' });
    expect(res.status).toBe(201);
    expect(res.body.id).toBeDefined();
  });
});
```

## Coverage: 80% minimum (`jest --coverage`)
