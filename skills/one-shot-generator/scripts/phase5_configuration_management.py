#!/usr/bin/env python3
"""
Phase 5 Microservices: Configuration Management

Configuration: Environment-specific settings.

Problem: Deploy same code to dev/staging/production
- Database: dev uses local, production uses AWS RDS
- API keys: dev uses test keys, production uses real keys
- Log level: dev uses DEBUG, production uses ERROR

Hardcoding breaks:
- Can't use same binary for all environments
- Secrets in code = security risk

Solution: Externalize configuration
- Code doesn't know environment
- Configuration from environment variables or config files
- Same code works everywhere
"""

from typing import Dict, Optional, Any
from datetime import datetime


def generate_config_manager() -> str:
    """Generate configuration management."""

    config = '''
class ConfigManager:
    """
    Manage configuration from multiple sources.

    Sources (priority order):
    1. Environment variables (override everything)
    2. .env file (local development)
    3. Config service (remote config)
    4. Defaults (hardcoded fallback)

    Example:
    LOG_LEVEL=DEBUG DATABASE_URL=postgres://... API_KEY=abc123
    """

    def __init__(self):
        self._config = {}
        self._config_sources = {}  # key → source

    def load_from_env(self) -> None:
        """Load from environment variables"""
        import os
        for key, value in os.environ.items():
            if key.startswith("APP_"):
                config_key = key[4:].lower()
                self._config[config_key] = value
                self._config_sources[config_key] = "env"

    def load_from_file(self, path: str) -> None:
        """Load from config file (.env or JSON)"""
        # Parse file and load
        pass

    def set_default(self, key: str, value: Any) -> None:
        """Set default value"""
        if key not in self._config:
            self._config[key] = value
            self._config_sources[key] = "default"

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get as boolean"""
        value = self._config.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    def get_int(self, key: str, default: int = 0) -> int:
        """Get as integer"""
        try:
            return int(self._config.get(key, default))
        except ValueError:
            return default
'''

    return config


def generate_config_system() -> dict:
    """Generate complete configuration system."""

    imports = '''from typing import Dict, Optional, Any
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Configuration Management: Environment-Specific Settings

Externalize configuration (12-factor app principle #3).

HIERARCHY:

1. ENVIRONMENT VARIABLES (highest priority)
   export LOG_LEVEL=DEBUG
   export DATABASE_URL=postgres://...
   export SECRET_KEY=abc123

2. .ENV FILE (local development)
   LOG_LEVEL=INFO
   DATABASE_URL=postgres://localhost
   (Never commit to git!)

3. CONFIG SERVICE (remote)
   ConsulAPI, etcd, AWS Parameter Store
   Central management, dynamic updates

4. DEFAULTS (lowest priority)
   LOG_LEVEL: "WARNING"
   PORT: 8000

EXAMPLE:

Development:
LOG_LEVEL=DEBUG
DATABASE_URL=postgres://localhost:5432/app_dev
API_KEY=test_key_12345
CACHE_ENABLED=false

Production:
LOG_LEVEL=ERROR
DATABASE_URL=postgres://prod-db.rds.amazonaws.com/app_prod
API_KEY=sk_live_abc123xyz
CACHE_ENABLED=true

CODE (same for all environments):
log_level = config.get("LOG_LEVEL", "WARNING")
db_url = config.get("DATABASE_URL")
api_key = config.get("API_KEY")

SAFETY:

Never hardcode secrets:
✗ password = "abc123"
✓ password = config.get("PASSWORD")

Secrets from environment:
✓ export DATABASE_PASSWORD=secure_pass
✓ Script reads from env, not code

Config validation:
✓ Start up → validate required keys present
✓ If missing: fail fast with clear error

DEPLOYMENT WORKFLOW:

1. Build: docker build → image
2. Deploy: push to staging
   - Set environment variables
   - Start container
   - Container reads from env
   - Uses staging DB, staging API keys
3. Deploy to production
   - Same image
   - Different environment variables
   - Uses production DB, real API keys
"""
'''

    config = generate_config_manager()

    complete_code = imports + module_doc + "\n" + config

    return {
        "code": complete_code,
        "pattern": "Configuration Management",
        "module": "phase5_configuration_management.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate configuration management")
    args = parser.parse_args()
    result = generate_config_system()
    print(result["code"])


if __name__ == "__main__":
    main()
