---
type: reference
last_verified: 2026-05-17
owner: claude
---

# Harness Agents Library

20 production-ready agents for Claude Code development.

## Agent Catalog

### Quality & Review (5 agents)
1. **code-reviewer** — Code quality, security, testing checks
2. **architect** — System design validation, consistency
3. **test-generator** — Test coverage analysis, test generation
4. **security-scanner** — OWASP checks, vulnerability detection
5. **performance-analyzer** — Latency, memory, optimization analysis

### Framework Experts (5 agents)
6. **django-expert** — Django patterns, migrations, DRF
7. **fastapi-expert** — Async correctness, Pydantic validation
8. **spring-expert** — Spring patterns, JPA, Spring Boot conventions
9. **go-expert** — Go idioms, goroutines, error handling
10. **node-expert** — TypeScript, async/await, NPM patterns

### Development Tools (5 agents)
11. **documentation-writer** — API docs, README, inline comments
12. **migration-helper** — Database migrations, zero-downtime changes
13. **refactoring-guide** — Legacy code modernization, debt reduction
14. **dependency-auditor** — Security vulnerabilities, version conflicts
15. **ci-cd-builder** — GitHub Actions, CI/CD pipelines, automation

### Data & Infrastructure (5 agents)
16. **schema-designer** — Database design, normalization, indexing
17. **graphql-builder** — GraphQL schema, resolvers, federation
18. **api-designer** — REST API design, versioning, deprecation
19. **config-manager** — Environment config, secrets management, 12-factor
20. **observability-setup** — Logging, metrics, tracing, monitoring

---

## How to Use Agents

### Invoke an Agent

```bash
/call:code-reviewer @/path/to/file.py
/call:architect --review system-design.md
/call:test-generator --analyze app/
```

### Create Custom Agents

1. Copy a template from agents-library/
2. Customize responsibilities
3. Add to .claude/agents/ in your project
4. Invoke: `/call:your-agent`

### Agent Development Workflow

1. **Planning**: Use architect agent to design system
2. **Implementation**: Use framework-specific expert
3. **Testing**: Use test-generator for coverage
4. **Review**: Use code-reviewer for quality
5. **Security**: Use security-scanner for vulnerabilities
6. **Documentation**: Use documentation-writer for docs
7. **Deployment**: Use ci-cd-builder for automation

---

## Agent Specifications (Quick Reference)

### 1. code-reviewer
**Input**: File path or code snippet  
**Output**: Approval or list of issues + fixes  
**Check time**: 1-2 minutes  
**Keywords**: quality, security, tests

### 2. architect
**Input**: System design doc or proposal  
**Output**: Design validation, suggestions  
**Check time**: 5-10 minutes  
**Keywords**: architecture, patterns, consistency

### 3. test-generator
**Input**: File path (source code)  
**Output**: Test coverage report, test templates  
**Check time**: 2-3 minutes  
**Keywords**: coverage, testing, fixtures

### 4. security-scanner
**Input**: File path or codebase  
**Output**: Vulnerabilities + severity + fixes  
**Check time**: 3-5 minutes  
**Keywords**: security, owasp, vulnerabilities

### 5. performance-analyzer
**Input**: Code file or configuration  
**Output**: Performance issues, optimization suggestions  
**Check time**: 2-3 minutes  
**Keywords**: performance, optimization, latency

### 6-10. Framework Experts (django, fastapi, spring, go, node)
**Input**: Code file or project structure  
**Output**: Framework-specific guidance + fixes  
**Check time**: 2-3 minutes each  
**Keywords**: [framework]-specific patterns

### 11. documentation-writer
**Input**: Code file or project  
**Output**: Documentation templates, API docs  
**Check time**: 3-5 minutes  
**Keywords**: docs, api-documentation, readme

### 12. migration-helper
**Input**: Database schema change request  
**Output**: Zero-downtime migration strategy  
**Check time**: 5-10 minutes  
**Keywords**: migrations, database, zero-downtime

### 13. refactoring-guide
**Input**: Legacy code file  
**Output**: Modernization suggestions with examples  
**Check time**: 5-10 minutes  
**Keywords**: refactoring, modernization, legacy

### 14. dependency-auditor
**Input**: Dependency list (requirements.txt, package.json, etc.)  
**Output**: Vulnerabilities, version updates, conflicts  
**Check time**: 2-3 minutes  
**Keywords**: dependencies, security, versions

### 15. ci-cd-builder
**Input**: Project type + requirements  
**Output**: GitHub Actions workflow, CI/CD configuration  
**Check time**: 5-10 minutes  
**Keywords**: ci-cd, automation, github-actions

### 16. schema-designer
**Input**: Data requirements or entity description  
**Output**: Database schema with indexes, normalization  
**Check time**: 5-10 minutes  
**Keywords**: database, schema, normalization

### 17. graphql-builder
**Input**: REST endpoints or data model  
**Output**: GraphQL schema with resolvers, federation  
**Check time**: 5-10 minutes  
**Keywords**: graphql, schema, federation

### 18. api-designer
**Input**: API requirements or existing endpoints  
**Output**: REST API design with versioning, deprecation  
**Check time**: 5-10 minutes  
**Keywords**: api, rest, design

### 19. config-manager
**Input**: Configuration requirements  
**Output**: Environment-based config setup, secrets handling  
**Check time**: 3-5 minutes  
**Keywords**: config, environment, secrets

### 20. observability-setup
**Input**: Application type + observability requirements  
**Output**: Logging, metrics, tracing configuration  
**Check time**: 5-10 minutes  
**Keywords**: observability, logging, metrics, tracing

---

## Agent Availability Schedule

| Phase | Status | Agents Available |
|-------|--------|---|
| **Phase 1** | ✅ Complete | 1-5 (code-reviewer through performance-analyzer) |
| **Phase 2** | 🚧 Building | 6-10 (framework experts) |
| **Phase 3** | 🚧 Coming | 11-15 (dev tools) |
| **Phase 4** | 🚧 Coming | 16-20 (data & infrastructure) |

---

## Getting Started

### 1. Import Agents to Your Project

```bash
cp -r .claude/agents-library/ your-project/.claude/agents/
```

### 2. Use Code Reviewer

```bash
/call:code-reviewer @src/main.py
```

### 3. Create Custom Agents

```bash
# Copy a template
cp .claude/agents/01-code-reviewer.md .claude/agents/custom-agent.md

# Edit for your needs
nano .claude/agents/custom-agent.md
```

### 4. Integrate with Harness

Add to `.claude/CLAUDE.md`:
```markdown
## Available Agents

- **code-reviewer**: Quality & security checks (see agents/01-code-reviewer.md)
- **your-custom-agent**: Custom functionality
```

---

## Contributing Agents

Have a custom agent that works well? Share it!

1. Document it following this template
2. Add to .claude/agents-library/
3. Test with real code
4. Submit via GitHub PR

**Agent Submission Requirements**:
- Clear description and use cases
- Example invocations
- Output format documentation
- Tested on at least 2 codebases

---

**Status**: Building (1-5 of 20 available, rest in development)  
**Last updated**: 2026-05-17
