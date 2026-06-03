---
type: policy
last_verified: 2026-06-03
owner: claude
version: v1.2.3
---

# Support Policy

## Overview

The one-shot-prompting plugin is solo-maintained. Support is best-effort
via GitHub. There is no SLA.

## Support Channels

### GitHub Issues
- **Bugs / feature requests / questions**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/issues
- **Discussions**: https://github.com/usmanmughaltaleemabad/One-Shot-Plugin/discussions

### Documentation
- **Install + first run**: [README.md](README.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Release history**: [CHANGELOG.md](CHANGELOG.md)
- **Skill authoring**: [docs/skill-authoring.md](docs/skill-authoring.md)
- **Testing**: [docs/testing.md](docs/testing.md)
- **Pipeline tier docs**: [docs/](docs/) (`tier{1,2,25,3,35-agentic,4-self-extending,5-observability}.md`)

### Examples
Example *prompts* (not runnable projects) under [examples/](examples/).
See [examples/README.md](examples/README.md) for what each shows.

## Release cadence

No fixed schedule. Patches ship when a fix lands; minors when a meaningful
feature lands. See [CHANGELOG.md](CHANGELOG.md) for the actual history.

## Known Limitations

- **Framework body-hint coverage**: FastAPI is the most mature. Django,
  Spring, NestJS, Go, Node.js have working hint sets but fewer edge cases.
- **Cost calibration**: Cost estimates are derived from a small sample of
  real generations; treat them as ballpark, not contractual.
- **External dependencies**: Python stdlib only at runtime; optional pip
  deps degrade gracefully when absent.

## Getting Help

1. Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — covers the common cases
2. Search existing issues
3. If still stuck, open an issue with: framework + version, the exact
   `/one-shot` command you ran, and any error output

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

---

**Last Updated**: 2026-05-25  
**Current Version**: v1.2.0 (Phase 3 + Phase 4 Complete)
