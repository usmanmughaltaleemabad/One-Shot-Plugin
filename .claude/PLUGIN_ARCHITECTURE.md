# Professional Plugin Harness Architecture

This plugin follows Anthropic's recommended structure for enterprise-grade Claude plugins.

## Architecture Principles

### 1. **Clean Root Directory**
- Only 3 files in root: `CLAUDE.md`, `README.md`, `.gitignore`
- All organizational/session docs → `.claude/` hierarchy
- Old docs automatically archived

### 2. **Isolated Contexts**
```
.claude/
├── settings.json          ← Automation & permissions
├── archive/               ← Historical docs (git-excluded)
├── commands/              ← Command & skill documentation
├── skills/                ← Reusable domain knowledge
├── projects/
│   └── {project}/
│       └── memory/        ← Auto-memory (persistent session context)
└── {other-configs}/
```

### 3. **Automated Doc Hygiene**

**Hooks in `.claude/settings.json` run after EVERY execution:**

| Hook | Trigger | Action |
|------|---------|--------|
| **Archive** | PostToolUse | Old status/audit docs → `.claude/archive/` |
| **Organize** | PostToolUse | Command docs → `.claude/commands/` |
| **Clean root** | PostToolUse | Remove stale docs from root |
| **Sync CLAUDE.md** | Write/Edit | Update timestamps from memory |
| **Update .gitignore** | PostToolUse | Exclude archived patterns |

**Result**: You never manually organize docs again. They flow to the right place automatically.

### 4. **CLAUDE.md as Living Roadmap**

**Stays under 100 lines** by:
- Linking to external docs (`@path/to/file`)
- Using memory for session context
- Storing skills in `.claude/skills/`
- Archiving old docs automatically

**Contains only**:
- Project status snapshot
- Architecture diagram (text)
- Roadmap tracker
- Links to detailed docs
- Quick start reference

### 5. **Auto-Memory for Session Continuity**

**Memory lives in** `.claude/projects/c--Projects-plugin/memory/MEMORY.md`

**Types tracked**:
- `user/` — Your role, preferences, knowledge
- `feedback/` — Rules you've taught Claude (do/don't patterns)
- `project/` — Current sprint, blockers, deadlines
- `reference/` — External systems (Linear, Grafana, etc.)

**Hooks sync CLAUDE.md with memory** — roadmap always reflects current truth.

## File Organization

### Committed to Git
```
plugin/
├── CLAUDE.md           ✅ Current roadmap & org
├── README.md           ✅ User guide
├── .gitignore          ✅ Excludes archives & old docs
├── .claude/
│   ├── settings.json   ✅ Automation hooks & permissions
│   ├── skills/         ✅ Reusable domain knowledge (versioned)
│   └── PLUGIN_ARCHITECTURE.md (this file)
└── one-shot-prompting/
    ├── source code     ✅ Core implementation
    ├── examples/       ✅ Integration examples
    └── tests/          ✅ Test suites
```

### NOT Committed (Auto-Organized)
```
.claude/
├── archive/            🔒 Gitignored - historical docs
├── commands/           🔒 Gitignored - command docs (if any)
├── projects/           🔒 Gitignored - auto-memory per project
└── *.local.json        🔒 Gitignored - personal overrides
```

## Workflow

### Starting a Session
1. Read `CLAUDE.md` — current status & roadmap
2. Check memory (`@memory/MEMORY.md`) — session context & prior decisions
3. Start work — hooks auto-organize output

### Completing a Phase
1. Update roadmap table in `CLAUDE.md`
2. Save phase summary to memory (hooks sync automatically)
3. Old docs auto-archive — no manual cleanup needed

### Onboarding a Team Member
1. Clone repo → `CLAUDE.md` tells them the story in 2 minutes
2. Read memory for decisions & context
3. Check `.claude/skills/` for domain knowledge
4. Archive is for reference only

## Anthropic Standards This Follows

✅ **Separation of concerns** — Code, org, session context isolated  
✅ **Scalability** — Archive old docs; keep root clean  
✅ **Transparency** — CLAUDE.md is the single source of truth  
✅ **Automation** — Hooks prevent doc rot; no manual work  
✅ **Session continuity** — Memory persists across conversations  
✅ **Clean git history** — Old docs archived, not committed  

## Customization

### Change Doc Cleanup Rules
Edit `.claude/settings.json` `PostToolUse` hooks → customize patterns

### Add Permissions
Edit `.claude/settings.json` `permissions.allow` → add new rules

### Create Custom Skills
Add `.claude/skills/{skill-name}/SKILL.md` → hooks will discover it

### Override Locally
Create `.claude/settings.local.json` (gitignored) → personal preferences

## When Hooks Fire

- **After Write/Edit/Bash**: Archive old docs, sync CLAUDE.md
- **Never manual cleanup**: All org is automated
- **Fast**: 5–15 seconds per execution (cached on subsequent runs)

## See Also
- `CLAUDE.md` — Current roadmap
- `README.md` — User guide
- `memory/MEMORY.md` — Session context (auto-loaded)
- `.claude/skills/` — Reusable domain knowledge
