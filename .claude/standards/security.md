---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Security Standards

Rules for secure code generation.

## GEN-003: OWASP Top 10 Compliance

**Rule:** All generated code must pass security scanning for OWASP Top 10 vulnerabilities.

**Top 10 Categories Scanned:**
1. Injection (SQL, OS, LDAP, etc.)
2. Broken Authentication
3. Sensitive Data Exposure
4. XML External Entities (XXE)
5. Access Control Bypass
6. Security Misconfiguration
7. Cross-Site Scripting (XSS)
8. Insecure Deserialization
9. Using Components with Known Vulnerabilities
10. Insufficient Logging & Monitoring

**Enforcement:** Reviewer agent runs bandit (Python) or semgrep (multi-language)

**Valid Example:**
```python
# ✅ Uses parameterized queries
def get_user(user_id: int) -> User:
    return db.query(User).filter(User.id == user_id).first()
```

**Invalid Example (caught by GEN-003):**
```python
# ❌ SQL injection vulnerability
def get_user(user_id: str) -> User:
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
```

## GEN-006: No Hardcoded Secrets

**Rule:** Generated code must not contain hardcoded credentials, API keys, or secrets.

**Scope:**
- Database passwords, API keys, OAuth tokens
- Private encryption keys
- AWS/Azure/GCP credentials

**Enforcement:** Hook: PostToolUse runs truffleHog (secret detection)

**Valid Example:**
```python
# ✅ Secrets from environment
db_password = os.getenv("DB_PASSWORD")
api_key = os.getenv("ANTHROPIC_API_KEY")
```

**Invalid Example (caught by GEN-006):**
```python
# ❌ Hardcoded secret
api_key = "sk-proj-abcdef123456"
db_password = "mysecret123"
```

**Exemption:** Mark with `@unsafe` only in test fixtures
```python
@pytest.fixture
def mock_api_key():  # @unsafe — test fixture only
    return "test-key-12345"
```
