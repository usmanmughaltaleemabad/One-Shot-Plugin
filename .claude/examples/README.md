---
type: guide
last_verified: 2026-05-17
owner: claude
---

# Harness Reference Implementations

These are working harness examples for different frameworks. Copy these to your project and customize.

## Available Templates

| Framework | File | Status | Features |
|-----------|------|--------|----------|
| **Django** | `DJANGO_HARNESS_TEMPLATE.md` | ✅ Complete | DRF, async, testing |
| **FastAPI** | `FASTAPI_HARNESS_TEMPLATE.md` | 🚧 Coming | SQLAlchemy async, pydantic |
| **Spring Boot** | `SPRING_HARNESS_TEMPLATE.md` | 🚧 Coming | JPA, testing, maven |
| **Go** | `GO_HARNESS_TEMPLATE.md` | 🚧 Coming | stdlib, Chi, postgres |
| **Node/Express** | `NODE_HARNESS_TEMPLATE.md` | 🚧 Coming | TypeScript, Jest, ORM |

## How to Use

### Option 1: Copy Template (Recommended)

```bash
# Copy Django template
cp .claude/examples/DJANGO_HARNESS_TEMPLATE.md your-project/.claude/CLAUDE.md

# Edit for your project
nano your-project/.claude/CLAUDE.md
```

### Option 2: Start from Scratch

```bash
# Initialize harness (coming soon)
claude harness init --framework django
```

## What Each Template Includes

1. **CLAUDE.md** — Router for your project
2. **standards/** — Coding standards for your framework
3. **agents/** — Code review, architecture, debugging agents
4. **hooks/** — Pre/post execution validation
5. **beads/** — State tracking examples

## Customization Guide

### 1. Update CLAUDE.md for Your Project

```markdown
# Your Project Name

[Update project-specific links and rules]
```

### 2. Adjust Standards for Your Team

If your team uses different standards:
- Edit `.claude/standards/code-style-{framework}.md`
- Adjust testing coverage (80% → 90%?)
- Add/remove security rules

### 3. Create Custom Agents

Add agents for your specific needs:
- Performance optimizer
- API designer
- Database schema reviewer
- DevOps engineer

### 4. Configure Hooks

Customize pre_tool_use.sh for your workflow:
- Block dangerous commands
- Enforce your standards
- Auto-format code

## Examples

### Using Django Template

```bash
# 1. Clone the plugin
git clone https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

# 2. Set up harness in your Django project
cp One-Shot-Plugin/one-shot-prompting/.claude/examples/DJANGO_HARNESS_TEMPLATE.md your-project/.claude/CLAUDE.md

# 3. Customize
cd your-project
nano .claude/CLAUDE.md  # Update for your project

# 4. Test
/one-shot-prompting:one-shot-generator "add user authentication" @.

# 5. Review generated code
# → Check tests pass
# → Check hooks are satisfied
# → Commit if happy
```

### Creating a Custom Agent

Add to `.claude/agents/my-agent.md`:

```markdown
---
name: my-agent
description: My custom agent for specific tasks
owner: your-name
---

## Responsibilities

[What your agent does]

## How to Invoke

```
/call:my-agent @/path/to/file
```
```

## FAQ

**Q: Can I mix templates?**  
A: Yes! You can combine standards/agents from different templates.

**Q: What if my framework isn't here?**  
A: Use the closest match and customize. Open an issue for new frameworks.

**Q: Can I share my harness?**  
A: Yes! Post it to the harness community. (Link coming soon)

**Q: How do I update templates?**  
A: Pull latest from: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin

---

**Status**: Reference implementations being expanded  
**Last updated**: 2026-05-17  
**Contributing**: Submit harnesses via GitHub PR
