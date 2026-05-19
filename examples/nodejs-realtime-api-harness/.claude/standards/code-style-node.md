---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Node.js / TypeScript Code Style

## Express route pattern

```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { SubscriptionService } from '../services/subscription.service';

const router = Router();
const svc = new SubscriptionService();

router.post('/', async (req: Request, res: Response, next: NextFunction) => {
  try {
    const sub = await svc.create(req.body);
    res.status(201).json(sub);
  } catch (err) {
    next(err);
  }
});
```

## Service layer

Business logic in `*.service.ts`. Routes only call services.

## Types

No `any`. Use interfaces or `z.infer<typeof schema>` (Zod).

## Async

Always `async/await`. No bare `.then()/.catch()` chains.
