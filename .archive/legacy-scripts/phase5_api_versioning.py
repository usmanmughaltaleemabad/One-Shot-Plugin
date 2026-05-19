#!/usr/bin/env python3
"""
Phase 5 Microservices: API Versioning

API Versioning: Support old + new APIs simultaneously.

Problem: Change API
- Old: GET /products → returns {id, name, price}
- New: GET /products → returns {id, name, price, rating, reviews}
- Old client: breaks (expects 3 fields)

Solution: Versioning
- v1: GET /v1/products → {id, name, price}
- v2: GET /v2/products → {id, name, price, rating, reviews}
- Old client: uses v1 (works)
- New client: uses v2 (works)
- Both coexist

Strategies:
- URL path: /v1/products vs /v2/products
- Accept header: Accept: application/vnd.api+json;version=2
- Query param: /products?version=2
"""

from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta


def generate_api_versioning() -> str:
    """Generate API versioning framework."""

    versioning = '''
class APIVersionManager:
    """
    Manage multiple API versions.

    v1: deprecated but still supported
    v2: current production
    v3: beta testing
    """

    def __init__(self):
        self._versions = {}  # version → handlers
        self._deprecated_versions = set()
        self._deprecated_at = {}  # version → date

    def register_version(
        self,
        version: str,
        handlers: Dict[str, Callable]
    ) -> None:
        """Register API version"""
        self._versions[version] = handlers

    def deprecate_version(
        self,
        version: str,
        sunset_date: datetime
    ) -> None:
        """Mark version as deprecated"""
        self._deprecated_versions.add(version)
        self._deprecated_at[version] = sunset_date

    def route_request(
        self,
        version: str,
        endpoint: str,
        request: Dict
    ) -> Dict:
        """Route request to correct version"""
        if version not in self._versions:
            return {
                "error": f"Version {version} not found",
                "status": 404
            }

        handlers = self._versions[version]

        if endpoint not in handlers:
            return {
                "error": f"Endpoint {endpoint} not found in version {version}",
                "status": 404
            }

        handler = handlers[endpoint]
        response = handler(request)

        # Add deprecation warning if deprecated
        if version in self._deprecated_versions:
            response["warning"] = f"API version {version} deprecated. Sunset: {self._deprecated_at[version]}"

        return response

    def get_active_versions(self) -> List[str]:
        """Get non-deprecated versions"""
        return [v for v in self._versions if v not in self._deprecated_versions]
'''

    return versioning


def generate_api_evolution() -> str:
    """Generate API evolution strategies."""

    evolution = '''
class APIEvolution:
    """
    Evolve API without breaking clients.

    Strategies:
    1. ADDITIVE: Add new optional fields
       - v1: {id, name}
       - v2: {id, name, category} - new optional field
       - Backward compatible

    2. RENAMING: Add new name, deprecate old
       - v1: {full_name}
       - v2: {full_name, firstName, lastName}
       - Support both

    3. VERSIONING: Create new version
       - v1: /v1/products → {id, name, price}
       - v2: /v2/products → {id, name, price, rating}
       - Eventually deprecate v1

    4. FEATURE TOGGLE: New API behind flag
       - Feature flag: new_api_enabled
       - Enable for 10% users first
       - Validate before rollout
    """

    def __init__(self):
        self._evolution_plan = []

    def add_optional_field(
        self,
        version: str,
        field: str,
        default_value=None
    ) -> None:
        """Add optional field to response"""
        self._evolution_plan.append({
            "type": "add_optional_field",
            "version": version,
            "field": field,
            "default": default_value,
            "date": datetime.utcnow().isoformat()
        })

    def deprecate_field(
        self,
        version: str,
        field: str,
        replacement: Optional[str] = None
    ) -> None:
        """Mark field as deprecated"""
        self._evolution_plan.append({
            "type": "deprecate_field",
            "version": version,
            "field": field,
            "replacement": replacement,
            "date": datetime.utcnow().isoformat()
        })

    def create_new_version(
        self,
        version: str,
        changes: List[str]
    ) -> None:
        """Create new API version"""
        self._evolution_plan.append({
            "type": "new_version",
            "version": version,
            "changes": changes,
            "date": datetime.utcnow().isoformat()
        })
'''

    return evolution


def generate_versioning_system() -> dict:
    """Generate complete API versioning system."""

    imports = '''from typing import Dict, Optional, List, Callable
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 API Versioning: Backward Compatibility

Support multiple API versions simultaneously.

VERSIONING STRATEGIES:

1. URL PATH (most common)
   GET /v1/products → version 1
   GET /v2/products → version 2
   - Clear in URL
   - Easy to deprecate

2. ACCEPT HEADER
   GET /products
   Accept: application/vnd.api+json;version=2
   - Cleaner URL
   - Complex for browsers

3. QUERY PARAMETER
   GET /products?version=2
   - Easy to test (link in browser)
   - Not RESTful

EVOLUTION TIMELINE:

v1 (October 2024):
- /v1/products → {id, name, price}

v2 (January 2025):
- /v2/products → {id, name, price, rating, reviews}
- /v1/products still works
- v1 clients: unaffected

v1 Deprecation (April 2025):
- Announce: "v1 sunset June 30"
- /v1/products → returns "Deprecated" header
- Emails to clients using v1
- Traffic monitoring

v1 Sunset (June 30):
- /v1/products → 404 error
- All clients must upgrade
- Safe because announced 3 months prior

COMMUNICATION:

Announce deprecation:
- Blog post: "API v1 will sunset in 3 months"
- Email: direct to clients
- Response header: "Deprecation: true"
- Rate limit increase: help with migration

Timeline:
- Month 0: Announce sunset date (3 months out)
- Month 1: Send email reminders
- Month 2: Send final notice
- Month 3: Shutdown

BACKWARDS COMPATIBILITY:

Always try to be additive:
✓ Add new field: old clients ignore it
✓ Add new endpoint: old clients don't use it
✓ Change internal format: expose same API

Avoid breaking:
✗ Remove field: old clients break
✗ Change type: int → string breaks old code
✗ Change semantics: "rating" now means something else
"""
'''

    versioning = generate_api_versioning()
    evolution = generate_api_evolution()

    complete_code = imports + module_doc + "\n" + versioning + "\n" + evolution

    return {
        "code": complete_code,
        "pattern": "API Versioning",
        "module": "phase5_api_versioning.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate API versioning")
    args = parser.parse_args()
    result = generate_versioning_system()
    print(result["code"])


if __name__ == "__main__":
    main()
