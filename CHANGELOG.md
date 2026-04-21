# Changelog

All notable changes to the One-Shot Prompting plugin are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/).

## [0.4.0] - 2026-04-21

### Added
- **Event versioning and schema evolution** (new)
  - Auto-generate backwards-compatible event schemas
  - Version migration helpers for event schema changes
  - Deprecation warnings in generated code
  - Request: "Add event versioning" or "Generate event schema"

- **Advanced error handling patterns** (new)
  - Circuit breaker implementation
  - Exponential backoff with jitter
  - Dead letter queue handling
  - Error telemetry and observability hooks
  - Request: "Include circuit breaker" or "Add dead letter queue"

- **Observability and monitoring** (new)
  - Structured logging templates
  - Distributed tracing integration (OpenTelemetry)
  - Metrics collection (Prometheus format)
  - Health check endpoints
  - Request: "Add observability" or "Include OpenTelemetry"

- **Security hardening** (new)
  - Input validation templates
  - Rate limiting strategies
  - Authentication/authorization patterns
  - Encryption helpers
  - Request: "Include security checks" or "Add authentication"

### Changed
- Assumptions block documents error handling strategy
- Generated code includes observability by default
- README includes runbook for debugging and monitoring

### Improved
- Production-ready error handling
- Complete observability stack
- Enterprise security patterns

## [0.3.0] - 2026-04-21

### Added
- **Deployment configuration generation** (new)
  - Docker Dockerfile with multi-stage builds (production-optimized)
  - Kubernetes manifests (Deployment, Service, ConfigMap)
  - Docker Compose for local development
  - Request in prompt: "Include Dockerfile", "Add Kubernetes manifests", "Include Docker Compose"

- **CI/CD pipeline templates** (new)
  - GitHub Actions workflows (.github/workflows/test.yml)
  - GitLab CI pipeline support
  - Automated test coverage reporting
  - Code scanning and security checks
  - Performance benchmarking setup
  - Request in prompt: "Generate GitHub Actions workflow" or "Add GitLab CI"

- **Enhanced documentation**
  - Environment variable templates
  - Deployment architecture diagrams in README
  - Security best practices per language
  - Performance optimization guidelines

- **Development ergonomics**
  - Hot-reload development setup hints
  - Local debugging configuration
  - Integration test setup instructions
  - Performance profiling helpers (Go pprof, Python cProfile, Node.js profiler)

### Changed
- Skill now prompts for deployment needs automatically
- README generation includes deployment section by default
- Assumptions block now documents deployment/CI-CD choices

### Improved
- Generated modules are now cloud-ready (12-factor app compliant)
- Better integration with modern DevOps workflows
- Comprehensive development-to-production guides

## [0.2.0] - 2026-04-21

### Added
- **Multi-language support**: Generate sidecars in Python, Go, Rust, JavaScript/TypeScript, and Java
  - Detect language from user prompt ("in Go", "Rust sidecar", etc.)
  - Default to Python if not specified
  - Each language uses idiomatic conventions and patterns
  
- **Type hints and type safety** across all languages
  - Python: Full type annotations on functions and variables
  - Go: Explicit types in function signatures
  - Rust: Strong typing with proper generics
  - TypeScript: Full type coverage with strict mode
  - Java: Generic types and proper annotations
  
- **Linting compliance by default**
  - Python: PEP 8 + Black + Flake8 compliant
  - Go: gofmt + go vet clean
  - Rust: clippy clean with default settings
  - TypeScript: eslint recommended config
  - Java: Google style guide compliant
  
- **Improved edge case handling**
  - Added handling for: null/None values, resource cleanup, timeouts, concurrent access
  - More comprehensive assumptions block documenting edge cases
  - Better documentation of NOT-handled scenarios
  
- **Language override in rerun hints**
  - Users can now rerun with "In Go" / "In Rust" / "In TypeScript" to regenerate in different language
  - Maintains all other assumptions and logic

### Changed
- Assumptions block now includes explicit language and code quality requirements
- Test examples include language-specific testing frameworks
- README generation includes language-specific adaptation notes
- Edge case enumeration expanded to include more realistic scenarios

### Improved
- Code quality: All generated modules now pass standard linting tools
- Robustness: Better handling of concurrent events, clock skew, resource cleanup
- Flexibility: Support for 5 languages instead of Python-only
- User experience: Clear rerun hints for language switching and code quality overrides

## [0.1.0] - 2026-04-21

### Initial Release
- One-shot feature generation for event-driven sidecars
- Single-prompt code generation with NO clarifying questions
- Assumptions block making all decisions visible
- Complete module, tests, README, and rerun hints in one response
- Python-only implementation
- Basic edge case handling
- Support for event-driven architectures with async buses
