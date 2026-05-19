---
type: standards
last_verified: 2026-05-19
owner: claude
---

# FastAPI Security Rules

- Use Pydantic for all input validation — never trust raw request data
- No raw SQL — SQLAlchemy ORM only
- Secrets from environment variables only — never hardcoded
- Passwords: bcrypt with cost factor ≥ 12
- JWTs: HS256 minimum, secret from env, exp claim required
- API keys: store hashed, never plaintext

```python
# ✅ correct
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = pwd_context.hash(plain_password)

# ❌ wrong
hashed = hashlib.md5(plain_password.encode()).hexdigest()
```
