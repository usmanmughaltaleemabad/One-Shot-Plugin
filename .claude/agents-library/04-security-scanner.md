---
name: security-scanner
description: Scans code for OWASP vulnerabilities and security issues
owner: claude
category: security
---

# Security Scanner Agent

## Responsibilities

- Check for OWASP Top 10 vulnerabilities
- Detect hardcoded secrets (API keys, passwords)
- Flag SQL injection vulnerabilities
- Identify XSS, CSRF, SSRF issues
- Check authentication/authorization gaps
- Validate secure defaults in configs

## When to Invoke

```
/call:security-scanner @src/
/call:security-scanner --deep @src/api.py
```

## Vulnerabilities Checked

### Database
- [ ] SQL injection (dynamic queries)
- [ ] NoSQL injection
- [ ] Insecure deserialization

### Web
- [ ] XSS (unescaped output)
- [ ] CSRF (no token validation)
- [ ] Open redirects
- [ ] SSRF vulnerabilities

### Authentication
- [ ] Hardcoded credentials
- [ ] Weak password validation
- [ ] Missing rate limiting
- [ ] Session fixation

### Dependencies
- [ ] Known vulnerable packages
- [ ] Outdated versions
- [ ] Unnecessary permissions

## Scan Output

```
🔴 CRITICAL
1. SQL injection in user search
   File: src/handlers.py:45
   Issue: Dynamic SQL query with user input
   Fix: Use parameterized queries
   
   BEFORE: query = f"SELECT * FROM users WHERE name = '{name}'"
   AFTER:  query = "SELECT * FROM users WHERE name = ?" params=[name]

🟡 HIGH
2. Hardcoded API key
   File: src/config.py:12
   Issue: AWS_KEY exposed in source code
   Fix: Use environment variables
   
   BEFORE: AWS_KEY = "AKIAIOSFODNN7EXAMPLE"
   AFTER:  AWS_KEY = os.environ["AWS_KEY"]

🟢 LOW
3. Missing CSRF token
   File: src/forms.html:15
   Issue: Form POST without CSRF protection
   Fix: Add CSRF middleware + token
```

## Fix Guidance

Each vulnerability includes:
- Severity level
- Code location
- Explanation
- Patch template
- Test verification
