"""
Phase 5.5: Legacy Modernization Generator

Generates legacy code modernization infrastructure:
- Strangler facade pattern
- API translation layers
- Data migration (ETL) scripts
- Incremental migration planning
"""

from typing import Dict


def generate_legacy_python() -> Dict[str, str]:
    """Generate Python legacy modernization infrastructure"""
    return {
        "strangler_adapter.py": '''"""Strangler pattern adapter for legacy system migration"""
import httpx
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StranglerAdapter:
    """Gradually replace legacy system with new one"""

    def __init__(self, legacy_url: str, new_app_url: str):
        self.legacy_url = legacy_url
        self.new_app_url = new_app_url
        self.routing_rules = {}  # Rules for which endpoints use new system
        self.migration_log = []

    def register_route(self, path: str, method: str = "GET"):
        """Register route as migrated to new system"""
        key = f"{method} {path}"
        self.routing_rules[key] = {
            "status": "new",
            "migrated_at": datetime.now().isoformat()
        }
        logger.info(f"Registered {key} as migrated")

    async def route_request(self,
                           path: str,
                           method: str = "GET",
                           data: Dict[str, Any] = None) -> Any:
        """Route request to legacy or new system"""
        key = f"{method} {path}"

        # Use new system if registered
        if key in self.routing_rules:
            logger.debug(f"Routing {key} to NEW system")
            return await self._call_new_system(path, method, data)

        # Fall back to legacy
        logger.debug(f"Routing {key} to LEGACY system")
        return await self._call_legacy_system(path, method, data)

    async def _call_new_system(self,
                               path: str,
                               method: str,
                               data: Dict = None) -> Any:
        """Call new system endpoint"""
        url = f"{self.new_app_url}{path}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"New system error: {e}, falling back to legacy")
            # Fall back to legacy on error
            return await self._call_legacy_system(path, method, data)

    async def _call_legacy_system(self,
                                 path: str,
                                 method: str,
                                 data: Dict = None) -> Any:
        """Call legacy system endpoint"""
        url = f"{self.legacy_url}{path}"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.request(method, url, json=data)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Legacy system error: {e}")
            raise

    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status"""
        total_routes = len(self.routing_rules) + 10  # Assume 10 total routes
        migrated_routes = len(self.routing_rules)
        percentage = (migrated_routes / total_routes) * 100 if total_routes > 0 else 0

        return {
            "total_routes": total_routes,
            "migrated_routes": migrated_routes,
            "percentage_complete": percentage,
            "migrated_endpoints": list(self.routing_rules.keys())
        }

# Usage example
async def main():
    strangler = StranglerAdapter(
        "http://legacy.local",
        "http://localhost:8000"
    )

    # Register migrated endpoints
    strangler.register_route("/users", "GET")
    strangler.register_route("/users", "POST")
    strangler.register_route("/posts", "GET")

    # Route requests
    result = await strangler.route_request("/users", "GET")
    print(f"Result: {result}")

    # Check status
    status = strangler.get_migration_status()
    print(f"Migration: {status['percentage_complete']:.1f}% complete")

if __name__ == "__main__":
    asyncio.run(main())
''',
        "etl_migration.py": '''"""ETL script for data migration from legacy to new system"""
import asyncio
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataMigration:
    """Orchestrate data migration from legacy to new system"""

    def __init__(self, legacy_db, new_db):
        self.legacy_db = legacy_db
        self.new_db = new_db
        self.migration_log: List[Dict] = []

    async def migrate_users(self) -> int:
        """Migrate users from legacy to new"""
        logger.info("Starting user migration...")

        try:
            # 1. Extract
            legacy_users = await self.legacy_db.fetch_all("users")
            logger.info(f"Extracted {len(legacy_users)} users")

            # 2. Transform
            transformed = [self._transform_user(u) for u in legacy_users]

            # 3. Load
            inserted = 0
            for user in transformed:
                try:
                    await self.new_db.insert("users", user)
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert user: {e}")

            self.migration_log.append({
                "entity": "users",
                "extracted": len(legacy_users),
                "inserted": inserted,
                "status": "completed"
            })

            logger.info(f"User migration completed: {inserted}/{len(legacy_users)}")
            return inserted

        except Exception as e:
            logger.error(f"User migration failed: {e}")
            return 0

    async def migrate_posts(self) -> int:
        """Migrate posts from legacy to new"""
        logger.info("Starting post migration...")

        try:
            legacy_posts = await self.legacy_db.fetch_all("posts")
            logger.info(f"Extracted {len(legacy_posts)} posts")

            transformed = [self._transform_post(p) for p in legacy_posts]

            inserted = 0
            for post in transformed:
                try:
                    await self.new_db.insert("posts", post)
                    inserted += 1
                except Exception as e:
                    logger.warning(f"Failed to insert post: {e}")

            self.migration_log.append({
                "entity": "posts",
                "extracted": len(legacy_posts),
                "inserted": inserted,
                "status": "completed"
            })

            logger.info(f"Post migration completed: {inserted}/{len(legacy_posts)}")
            return inserted

        except Exception as e:
            logger.error(f"Post migration failed: {e}")
            return 0

    async def run_full_migration(self):
        """Run complete migration"""
        logger.info("Starting full data migration...")

        await self.migrate_users()
        await self.migrate_posts()

        logger.info("Full migration completed")
        return self.migration_log

    def _transform_user(self, legacy_user: Dict[str, Any]) -> Dict[str, Any]:
        """Transform user data from legacy format to new"""
        return {
            "id": legacy_user.get("user_id"),
            "name": legacy_user.get("name"),
            "email": legacy_user.get("email_address"),
            "created_at": legacy_user.get("created"),
            "legacy_id": legacy_user.get("user_id")
        }

    def _transform_post(self, legacy_post: Dict[str, Any]) -> Dict[str, Any]:
        """Transform post data from legacy format to new"""
        return {
            "id": legacy_post.get("post_id"),
            "title": legacy_post.get("title"),
            "content": legacy_post.get("body"),
            "author_id": legacy_post.get("user_id"),
            "created_at": legacy_post.get("published_date"),
            "legacy_id": legacy_post.get("post_id")
        }
''',
        "dead_code_detector.py": '''"""Detect unused/dead code in legacy system"""
import re
from typing import List, Dict, Set
from pathlib import Path

class DeadCodeDetector:
    """Identify unused code and functions"""

    def __init__(self, codebase_path: str):
        self.codebase_path = Path(codebase_path)
        self.definitions: Dict[str, Set[str]] = {}
        self.usages: Dict[str, Set[str]] = {}

    def scan(self):
        """Scan codebase for definitions and usages"""
        for py_file in self.codebase_path.rglob("*.py"):
            self._analyze_file(py_file)

    def _analyze_file(self, filepath: Path):
        """Analyze single Python file"""
        with open(filepath, 'r') as f:
            content = f.read()

        # Find function definitions
        functions = re.findall(r'^def\\s+(\\w+)\\s*\\(', content, re.MULTILINE)
        if functions:
            self.definitions[str(filepath)] = set(functions)

        # Find function calls
        calls = re.findall(r'(\\w+)\\s*\\(', content)
        self.usages[str(filepath)] = set(calls)

    def find_dead_code(self) -> Dict[str, List[str]]:
        """Find functions that are defined but never called"""
        dead_code = {}

        all_definitions = set()
        all_usages = set()

        for definitions in self.definitions.values():
            all_definitions.update(definitions)

        for usages in self.usages.values():
            all_usages.update(usages)

        # Find unused definitions
        unused = all_definitions - all_usages

        return {
            "unused_functions": list(unused),
            "total_functions": len(all_definitions),
            "percentage_dead": (len(unused) / len(all_definitions) * 100) if all_definitions else 0
        }
''',
    }


def generate_legacy(framework: str, language: str, app_name: str = None) -> Dict[str, str]:
    """Generate complete legacy modernization infrastructure"""
    app_name = app_name or "legacy-modernization"
    output = {}

    output.update(generate_legacy_python())

    # Migration plan template
    output["MIGRATION_PLAN.md"] = f'''# Legacy System Migration Plan for {app_name}

## Phase 1: Analysis (Week 1-2)
- [ ] Document all legacy endpoints
- [ ] Map dependencies
- [ ] Identify critical paths
- [ ] Estimate effort for each endpoint

## Phase 2: Foundation (Week 3-4)
- [ ] Set up new infrastructure
- [ ] Implement strangler adapter
- [ ] Deploy parallel systems
- [ ] Set up monitoring

## Phase 3: Migration (Week 5-8)
- [ ] Migrate endpoints in priority order
- [ ] Run ETL for data migration
- [ ] Implement API translation layers
- [ ] Test each migrated feature

## Phase 4: Completion (Week 9-10)
- [ ] Migrate remaining endpoints
- [ ] Remove legacy code
- [ ] Performance optimization
- [ ] Documentation update

## Risks & Mitigation

### Data Loss
- Backup all legacy data before migration
- Run parallel systems until stable

### Performance Regression
- Load test new system
- Monitor metrics continuously

### User Impact
- Gradual migration (strangler pattern)
- Feature flags for rollback

## Success Criteria
- All endpoints migrated
- No data loss
- Performance maintained or improved
- Zero downtime migration
'''

    return output
