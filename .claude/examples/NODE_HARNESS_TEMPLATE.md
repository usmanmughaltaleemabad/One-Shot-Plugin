---
type: example
last_verified: 2026-05-17
owner: claude
---

# Node.js Project Harness Template

**Framework**: Node 18+, Express/TypeScript, SQLAlchemy-like ORM  
**Features**: Async/await, type safety, testing

## .claude/CLAUDE.md

```markdown
---
type: router
last_verified: 2026-05-17
owner: claude
---

# Node.js Express Project

## Quick Links

| For... | See... |
|--------|--------|
| Code style | `.claude/standards/code-style-node.md` |
| Testing | `.claude/standards/testing-rules.md` |
| Security | `.claude/standards/security-rules.md` |

## Critical Rules

1. Use TypeScript for all new code
2. All endpoints are async (async/await)
3. Error handling with try/catch in async handlers
4. Use middleware for authentication
5. Tests: 80%+ coverage with Jest
```

## .claude/standards/code-style-node.md

```markdown
# Node.js Code Style

## Express Routes (TypeScript)

```typescript
import express, { Request, Response } from 'express';
import { UserService } from './services';

const router = express.Router();
const userService = new UserService();

router.get('/users', async (req: Request, res: Response) => {
    try {
        const users = await userService.listUsers();
        res.json(users);
    } catch (error) {
        res.status(500).json({ error: 'Internal server error' });
    }
});

router.post('/users', async (req: Request, res: Response) => {
    try {
        const { email, name } = req.body;
        const user = await userService.createUser({ email, name });
        res.status(201).json(user);
    } catch (error) {
        res.status(400).json({ error: 'Invalid request' });
    }
});

export default router;
```

## Service Layer

```typescript
import { AppDataSource } from './database';
import { User } from './entities/User';

export class UserService {
    private userRepository = AppDataSource.getRepository(User);
    
    async listUsers(): Promise<User[]> {
        return this.userRepository.find();
    }
    
    async createUser(data: { email: string; name: string }): Promise<User> {
        const user = this.userRepository.create(data);
        return this.userRepository.save(user);
    }
}
```

## TypeORM Entity

```typescript
import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn } from 'typeorm';

@Entity('users')
export class User {
    @PrimaryGeneratedColumn()
    id: number;
    
    @Column({ unique: true })
    email: string;
    
    @Column()
    name: string;
    
    @CreateDateColumn()
    createdAt: Date;
}
```
```

## .claude/standards/testing-rules.md

```markdown
# Node.js Testing (Jest)

## Minimum Coverage: 80%

```bash
npm test -- --coverage
```

## Test Pattern

```typescript
import { UserService } from './services';

describe('UserService', () => {
    let service: UserService;
    
    beforeEach(() => {
        service = new UserService();
    });
    
    test('should list users', async () => {
        const users = await service.listUsers();
        expect(Array.isArray(users)).toBe(true);
    });
    
    test('should create user', async () => {
        const user = await service.createUser({
            email: 'test@example.com',
            name: 'Test User',
        });
        expect(user.email).toBe('test@example.com');
    });
});
```
```

## .claude/standards/security-rules.md

```markdown
# Node.js Security

## SQL Injection Prevention

```typescript
// ❌ WRONG
const query = `SELECT * FROM users WHERE id = ${userId}`;

// ✅ CORRECT (TypeORM handles parameterization)
const user = await userRepository.findOne({ where: { id: userId } });
```

## Input Validation

```typescript
import { body, validationResult } from 'express-validator';

app.post('/users', 
    body('email').isEmail(),
    body('name').notEmpty(),
    async (req, res) => {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({ errors: errors.array() });
        }
        // Process request
    }
);
```

## Secrets Management

```typescript
import dotenv from 'dotenv';

dotenv.config();

const dbPassword = process.env.DB_PASSWORD;
if (!dbPassword) {
    throw new Error('DB_PASSWORD not set');
}
```
```

## Package.json

```json
{
    "name": "express-app",
    "version": "1.0.0",
    "scripts": {
        "dev": "tsx watch src/index.ts",
        "build": "tsc",
        "start": "node dist/index.js",
        "test": "jest",
        "lint": "eslint ."
    },
    "devDependencies": {
        "@types/express": "^4.17.17",
        "@types/node": "^20.0.0",
        "typescript": "^5.0.0",
        "jest": "^29.0.0",
        "eslint": "^8.0.0"
    },
    "dependencies": {
        "express": "^4.18.2",
        "typeorm": "^0.3.0",
        "pg": "^8.10.0"
    }
}
```
