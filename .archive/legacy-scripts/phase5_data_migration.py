#!/usr/bin/env python3
"""
Phase 5 Legacy Modernization: Data Migration

Problem: Migrate data from old system to new system.

Old system: MongoDB, documents {user_id, name, email}
New system: PostgreSQL, tables (users, orders, profiles)

Challenges:
- Data inconsistency (old system has bugs)
- Schema mismatch (field names, types)
- Volume (1B records)
- Downtime (can't migrate while running)
- Rollback (what if migration fails?)

Strategy:
- Phase 1: Copy old data to new (dual write)
- Phase 2: Validate (compare old vs new)
- Phase 3: Cutover (switch to new)
- Phase 4: Cleanup (archive old)
"""

from typing import Dict, List, Optional, Callable
from datetime import datetime


def generate_data_migration() -> str:
    """Generate data migration framework."""

    migration = '''
class DataMigration:
    """
    Migrate data from old system to new.

    Phases:
    1. Setup: prepare target schema
    2. Extract: read from old system
    3. Transform: convert format
    4. Load: write to new system
    5. Validate: compare old vs new
    6. Cutover: switch to new
    7. Cleanup: archive old
    """

    def __init__(self, source_db, target_db):
        self.source = source_db
        self.target = target_db
        self._migration_log = []
        self._errors = []

    def extract_data(self, table: str, batch_size: int = 1000) -> List[Dict]:
        """Extract data from old system"""
        # Read from source database
        records = self.source.query(f"SELECT * FROM {table}")
        return list(records)

    def transform_record(self, record: Dict, schema_mapping: Dict) -> Dict:
        """Transform record from old schema to new"""
        transformed = {}

        for old_field, new_field in schema_mapping.items():
            if old_field in record:
                # Apply transformation (type conversion, etc.)
                value = record[old_field]
                transformed[new_field] = self._convert_type(value)

        return transformed

    def load_data(self, table: str, records: List[Dict], batch_size: int = 1000) -> int:
        """Load data to new system"""
        loaded = 0

        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                self.target.insert_batch(table, batch)
                loaded += len(batch)
            except Exception as e:
                self._errors.append({
                    "batch": i,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                })

        return loaded

    def validate_migration(self, table: str) -> Dict:
        """Validate old vs new data"""
        old_count = self.source.count(table)
        new_count = self.target.count(table)

        return {
            "table": table,
            "old_count": old_count,
            "new_count": new_count,
            "match": old_count == new_count,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _convert_type(self, value):
        """Convert data types"""
        # int, str, datetime, etc.
        return value
'''

    return migration


def generate_dual_write() -> str:
    """Generate dual-write pattern for zero-downtime migration."""

    dual = '''
class DualWriteOrchestrator:
    """
    Write to both old and new system simultaneously.

    Allows zero-downtime migration:
    1. Enable dual-write (write to both)
    2. Migrate existing data (old → new)
    3. Migrate reads (old → new)
    4. Stop old system
    """

    def __init__(self, old_db, new_db):
        self.old = old_db
        self.new = new_db

    def create_user(self, user_data: Dict) -> str:
        """Create user in both systems"""
        # Write to old (source of truth for now)
        old_id = self.old.create_user(user_data)

        # Write to new (for validation)
        try:
            new_id = self.new.create_user(user_data)
            if old_id != new_id:
                # Log divergence
                pass
        except Exception as e:
            # New system failed, log but continue with old
            pass

        return old_id

    def update_user(self, user_id: str, updates: Dict) -> None:
        """Update user in both systems"""
        self.old.update_user(user_id, updates)

        try:
            self.new.update_user(user_id, updates)
        except Exception:
            pass

    def delete_user(self, user_id: str) -> None:
        """Delete user from both systems"""
        self.old.delete_user(user_id)

        try:
            self.new.delete_user(user_id)
        except Exception:
            pass
'''

    return dual


def generate_migration_system() -> dict:
    """Generate complete migration system."""

    imports = '''from typing import Dict, List, Optional, Callable
from datetime import datetime


'''

    module_doc = '''"""
Phase 5 Data Migration: Zero-Downtime System Switchover

Migrate from old to new system without downtime.

CHALLENGE: 1 billion records

Old system: MongoDB (sharded)
New system: PostgreSQL (replicated)

APPROACH: Dual-write + Gradual cutover

PHASE 1: DUAL-WRITE (Week 1)
- New code writes to both old + new
- Reads still from old (source of truth)
- Validation: compare old vs new nightly
- Issues: catch early, fix code

PHASE 2: BACKFILL (Weeks 2-3)
- Migrate existing data: old → new
- Batch: 10M records/day
- Validation: row counts match
- If issues: fix data, restart batch

PHASE 3: READ MIGRATION (Week 4)
- Route some reads to new (10%)
- Compare results (old vs new)
- Increase: 25%, 50%, 75%, 100%
- Monitor: latency, errors, correctness

PHASE 4: CUTOVER (Week 5)
- 100% reads from new
- Keep dual-write for safety
- Monitor for issues
- Keep old for 1 week (rollback plan)

PHASE 5: CLEANUP (Week 6)
- Disable dual-write
- Archive old system
- Decommission hardware

VALIDATION AT EACH PHASE:
- Row counts: old_count == new_count
- Checksums: hash(old_data) == hash(new_data)
- Sampling: spot-check 0.1% of records
- Business metrics: same results

ROLLBACK PLAN:
- Dual-write phase: turn off, readers revert
- Backfill phase: delete new data, retry
- Read migration: route back to old
- Cutover: route all to old
"""
'''

    migration = generate_data_migration()
    dual = generate_dual_write()

    complete_code = imports + module_doc + "\n" + migration + "\n" + dual

    return {
        "code": complete_code,
        "pattern": "Data Migration",
        "module": "phase5_data_migration.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate data migration system")
    args = parser.parse_args()
    result = generate_migration_system()
    print(result["code"])


if __name__ == "__main__":
    main()
