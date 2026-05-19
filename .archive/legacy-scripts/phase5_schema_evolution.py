#!/usr/bin/env python3
"""
Phase 5 Legacy Modernization: Schema Evolution

Schema evolution: Change database schema without breaking clients.

Problem: Add new column to table
- Old app expects: {id, name, email}
- Add: phone
- New schema: {id, name, email, phone}
- Old app: can't read, crashes

Solution: Backward/Forward compatible schema
- Old app: ignores phone (doesn't crash)
- New app: uses phone
- Both work simultaneously

Strategies:
- Additive: add columns (backward compatible)
- Deletive: remove columns (hard)
- Renaming: rename columns (use aliases)
- Type changes: int → string (risky)
"""

from typing import Dict, Optional, List
from datetime import datetime


def generate_schema_versioning() -> str:
    """Generate schema versioning."""

    versioning = '''
class SchemaVersion:
    """
    Track schema versions and migrations.

    v1: {id, name, email}
    v2: {id, name, email, phone} - additive
    v3: {id, name, email, phone, created_at} - additive
    v4: {id, name, email_address, phone, created_at} - renamed email to email_address
    """

    def __init__(self):
        self._schemas = {}  # version → schema
        self._migrations = []  # v1 → v2, v2 → v3, etc.

    def define_schema(self, version: int, fields: List[str]) -> None:
        """Define schema for version"""
        self._schemas[version] = {
            "version": version,
            "fields": fields,
            "created_at": datetime.utcnow().isoformat()
        }

    def add_migration(
        self,
        from_version: int,
        to_version: int,
        migration_func
    ) -> None:
        """Add migration between versions"""
        self._migrations.append({
            "from": from_version,
            "to": to_version,
            "migration": migration_func
        })

    def migrate_record(self, record: Dict, from_v: int, to_v: int) -> Dict:
        """Migrate record from old version to new"""
        for migration in self._migrations:
            if migration["from"] == from_v and migration["to"] == to_v:
                return migration["migration"](record)

        return record

    def is_backward_compatible(self, from_v: int, to_v: int) -> bool:
        """Check if new schema backward compatible"""
        if from_v >= to_v:
            return True

        # Additive changes are backward compatible
        old_fields = set(self._schemas[from_v]["fields"])
        new_fields = set(self._schemas[to_v]["fields"])

        # New fields are superset of old fields
        return old_fields.issubset(new_fields)
'''

    return versioning


def generate_schema_patterns() -> str:
    """Generate schema evolution patterns."""

    patterns = '''
class SchemaEvolutionPatterns:
    """
    Common schema evolution patterns.

    1. ADDITIVE: Add new field
       - Old app: ignores field
       - New app: uses field
       - Safe: backward compatible

    2. OPTIONAL: Make field optional
       - Old: required field
       - New: optional (default value)
       - Safe: backward compatible

    3. RENAME: Rename field
       - Old: name
       - New: full_name
       - Use: alias or dual fields
       - Migration: data from name → full_name

    4. SPLIT: Split field
       - Old: full_name
       - New: first_name, last_name
       - Migration: parse full_name
       - Risky: might fail

    5. MERGE: Merge fields
       - Old: first_name, last_name
       - New: full_name
       - Migration: concat
       - Risky: information loss
    """

    def __init__(self):
        self._applied_migrations = []

    def add_field_safe(self, table: str, field: str, default=None) -> None:
        """Safely add field"""
        # 1. Add column (NULL allowed)
        # 2. Populate with default value
        # 3. Backfill existing rows
        # 4. Update app to use new field

        migration = {
            "table": table,
            "field": field,
            "type": "add_field",
            "default": default,
            "applied_at": datetime.utcnow().isoformat()
        }

        self._applied_migrations.append(migration)

    def rename_field(self, table: str, old_name: str, new_name: str) -> None:
        """Safely rename field"""
        # 1. Add new field (copy old)
        # 2. Update app to read from new, write to both
        # 3. Backfill: old → new
        # 4. Update app to read from new only
        # 5. Drop old field

        migration = {
            "table": table,
            "from": old_name,
            "to": new_name,
            "type": "rename_field",
            "applied_at": datetime.utcnow().isoformat()
        }

        self._applied_migrations.append(migration)

    def get_migration_plan(self) -> List[Dict]:
        """Get migration history"""
        return self._applied_migrations.copy()
'''

    return patterns


def generate_schema_system() -> dict:
    """Generate complete schema evolution system."""

    imports = '''from typing import Dict, Optional, List
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Schema Evolution: Database Schema Versioning

Change database schema without breaking clients.

CHALLENGE: Update schema while system running

Old App (v1):
- Reads: {id, name, email}
- Expects: 3 fields
- Crashes if: field missing

New Code (v2):
- Needs: {id, name, email, phone}
- Must add: phone field
- Can't drop: breaks old app

SOLUTION: Expand-Contract Pattern

1. EXPAND
   - Add new field: phone
   - Old app: ignores it
   - New app: uses it
   - Both work: backward compatible

2. Migrate Data
   - Backfill: populate phone for existing records
   - Can be async (background job)

3. CONTRACT
   - Old app: gone (no longer using old schema)
   - Remove old field: safe now

TIMELINE:

Day 1: Deploy new code with EXPAND
- Code: if phone exists: use it, else use default
- Database: add phone column (nullable)
- Old version: works (phone ignored)
- New version: works (phone used)

Day 2-3: Backfill
- Background job: populate phone from contacts
- No app changes needed
- Can run 24/7

Day 4: Ensure old app deprecated
- All instances running new version
- Old version: no longer running

Day 5: Deploy code without old schema handling
- Remove: if phone exists check
- Assume: phone always present

Day 6: CONTRACT
- Remove phone from write (if migrating elsewhere)
- Delete old column (if truly gone)

BACKWARD COMPATIBILITY:

Safe:
✓ Add field (additive)
✓ Make field optional
✓ Add new table
✓ Add new index

Risky:
✗ Delete field (old app breaks)
✗ Rename field (old app breaks)
✗ Change field type (old app breaks)
✗ Add NOT NULL constraint (NULL values break)

EXAMPLE: Add phone field

Step 1: Expand
ALTER TABLE users ADD phone VARCHAR(20) NULL;
-- No app changes needed

Step 2: Migrate
UPDATE users SET phone = '555-0000';
-- Or: background job over days

Step 3: Contract
ALTER TABLE users MODIFY phone VARCHAR(20) NOT NULL;
-- Now required (assume all filled)
"""
'''

    versioning = generate_schema_versioning()
    patterns = generate_schema_patterns()

    complete_code = imports + module_doc + "\n" + versioning + "\n" + patterns

    return {
        "code": complete_code,
        "pattern": "Schema Evolution",
        "module": "phase5_schema_evolution.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate schema evolution patterns")
    args = parser.parse_args()
    result = generate_schema_system()
    print(result["code"])


if __name__ == "__main__":
    main()
