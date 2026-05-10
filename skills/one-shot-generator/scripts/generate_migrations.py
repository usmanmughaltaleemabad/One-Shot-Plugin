#!/usr/bin/env python3
"""
Gap 3: Database Migration Generation

Auto-generates database migrations when models change:
- Django: Creates migration files for new models with field args, chained dependencies
- FastAPI/SQLAlchemy: Creates Alembic migration files with real op.create_table() calls
- Spring/Hibernate: Creates Flyway SQL migration files with full field extraction
- Go: Creates migration files for configured migration tool with full schema

Input: New models (Python/Java/Go code), framework, project root
Output: Migration file(s) ready to apply
"""

import os
import re
import datetime
import argparse
from typing import List, Tuple, Dict, Optional
import hashlib
from pathlib import Path
import sys

# Shared library imports
sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import __version__, setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class MigrationGenerator:
    """Generates database migrations for new models."""

    def __init__(self, framework: str, project_root: str):
        self.framework = framework.lower()
        self.project_root = project_root
        self.timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def generate_migration(self, models_code: str, feature_name: str) -> Tuple[str, str]:
        """
        Generate a migration for new models.

        Args:
            models_code: Generated models file content
            feature_name: Feature name for migration name

        Returns:
            (migration_filepath, migration_content)
        """

        if self.framework == 'django':
            return self._generate_django_migration(models_code, feature_name)
        elif self.framework == 'fastapi':
            return self._generate_alembic_migration(models_code, feature_name)
        elif self.framework == 'spring':
            return self._generate_flyway_migration(models_code, feature_name)
        elif self.framework == 'go':
            return self._generate_go_migration(models_code, feature_name)
        else:
            return None, None

    def _generate_django_migration(self, models_code: str, feature_name: str) -> Tuple[str, str]:
        """Generate Django migration file with dependency chaining."""

        # Find existing migration number and get previous migration
        migrations_dir = os.path.join(self.project_root, 'app', 'migrations')
        migration_number = self._get_next_migration_number(migrations_dir)
        previous_migration = self._get_previous_django_migration(migrations_dir, migration_number)

        # Extract model classes from code
        models = self._extract_django_models(models_code)

        # Generate migration content
        migration_content = self._generate_django_migration_content(models, migration_number, previous_migration)

        # Migration filepath
        feature_slug = feature_name.lower().replace(' ', '_')
        migration_file = f"app/migrations/{migration_number:04d}_{feature_slug}.py"

        return migration_file, migration_content

    def _generate_alembic_migration(self, models_code: str, feature_name: str) -> Tuple[str, str]:
        """Generate Alembic (SQLAlchemy) migration file."""

        # Extract table info from models
        tables = self._extract_sqlalchemy_tables(models_code)

        # Generate migration content
        migration_content = self._generate_alembic_migration_content(tables)

        # Migration filepath
        feature_slug = feature_name.lower().replace(' ', '_')
        migration_file = f"alembic/versions/{self.timestamp}_{feature_slug}.py"

        return migration_file, migration_content

    def _generate_flyway_migration(self, models_code: str, feature_name: str) -> Tuple[str, str]:
        """Generate Flyway SQL migration file."""

        # Extract table info from code
        tables = self._extract_spring_entities(models_code)

        # Generate SQL
        sql_content = self._generate_flyway_sql(tables, feature_name)

        # Migration filepath
        feature_slug = feature_name.lower().replace(' ', '_')
        version = self._get_flyway_version()
        migration_file = f"src/main/resources/db/migration/V{version}_{feature_slug}.sql"

        return migration_file, sql_content

    def _generate_go_migration(self, models_code: str, feature_name: str) -> Tuple[str, str]:
        """Generate Go migration file (for golang-migrate or similar)."""

        # Extract table info from Go models
        tables = self._extract_go_tables(models_code)

        # Generate SQL
        sql_content = self._generate_go_migration_sql(tables)

        # Migration filepath
        timestamp = datetime.datetime.now().strftime("%Y%m%d150405")
        feature_slug = feature_name.lower().replace(' ', '_')
        migration_file = f"db/migrations/{timestamp}_{feature_slug}.up.sql"

        return migration_file, sql_content

    # Helper methods

    def _get_next_migration_number(self, migrations_dir: str) -> int:
        """Get next migration number for Django."""
        if not os.path.exists(migrations_dir):
            return 1

        migrations = [f for f in os.listdir(migrations_dir) if f[0].isdigit()]
        if not migrations:
            return 1

        latest = max([int(f.split('_')[0]) for f in migrations])
        return latest + 1

    def _get_previous_django_migration(self, migrations_dir: str, current_number: int) -> Optional[str]:
        """Get the previous migration name for dependency chaining."""
        if not os.path.exists(migrations_dir) or current_number <= 1:
            return None

        previous_number = current_number - 1
        app_label = 'app'  # TODO: auto-detect from INSTALLED_APPS

        # Return migration reference in Django format
        return f"('{app_label}', '{previous_number:04d}_auto')"

    def _get_flyway_version(self) -> str:
        """Get next Flyway version number."""
        versions_dir = os.path.join(self.project_root, 'src/main/resources/db/migration')
        if not os.path.exists(versions_dir):
            return "1"

        files = os.listdir(versions_dir)
        if not files:
            return "1"

        versions = []
        for f in files:
            match = re.match(r'V(\d+)', f)
            if match:
                versions.append(int(match.group(1)))

        return str(max(versions) + 1) if versions else "1"

    def _extract_django_models(self, code: str) -> List[Dict]:
        """Extract Django model definitions from code, preserving field arguments."""
        models = []

        # Find class definitions that inherit from models.Model
        pattern = r'class\s+(\w+)\(models\.Model\):(.*?)(?=class\s|\Z)'
        matches = re.finditer(pattern, code, re.DOTALL)

        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)

            # Extract fields with full arguments
            fields = []
            # Match field definitions, capturing the full argument list
            field_pattern = r'(\w+)\s*=\s*models\.(\w+)\((.*?)\)(?:\n|\s|$)'
            field_matches = re.finditer(field_pattern, class_body, re.DOTALL)

            for fm in field_matches:
                field_name = fm.group(1)
                field_type = fm.group(2)
                field_args = fm.group(3).strip()

                # Clean up args (remove extra whitespace, normalize)
                field_args = ' '.join(field_args.split())

                fields.append({
                    'name': field_name,
                    'type': field_type,
                    'args': field_args if field_args else ''
                })

            models.append({
                'name': class_name,
                'fields': fields
            })

        return models

    def _generate_django_migration_content(self, models: List[Dict], number: int, previous_migration: Optional[str] = None) -> str:
        """Generate Django migration file content with field arguments preserved."""

        operations = []

        for model in models:
            fields = []
            for field in model['fields']:
                args = field.get('args', '')
                if args:
                    field_def = f"('{field['name']}', models.{field['type']}({args}))"
                else:
                    field_def = f"('{field['name']}', models.{field['type']}())"
                fields.append(field_def)

            fields_str = ',\n                '.join(fields)

            operation = f"""migrations.CreateModel(
            name='{model['name']}',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                {fields_str},
            ],
        )"""

            operations.append(operation)

        operations_str = ',\n        '.join(operations)

        # Build dependencies list
        dependencies_str = ""
        if previous_migration:
            dependencies_str = f"        '{previous_migration}',"
        else:
            dependencies_str = "        # Empty for first migration, or chain to previous"

        content = f'''# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
{dependencies_str}
    ]

    operations = [
        {operations_str}
    ]
'''

        return content

    def _extract_sqlalchemy_tables(self, code: str) -> List[Dict]:
        """Extract SQLAlchemy table definitions with full column info."""
        tables = []

        # Find class definitions
        pattern = r'class\s+(\w+)\(Base\):(.*?)(?=class\s|\Z)'
        matches = re.finditer(pattern, code, re.DOTALL)

        for match in matches:
            class_name = match.group(1)
            class_body = match.group(2)

            # Extract __tablename__
            tablename_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', class_body)
            tablename = tablename_match.group(1) if tablename_match else class_name.lower()

            # Extract Column definitions
            columns = []
            col_pattern = r'(\w+)\s*=\s*Column\((.*?)\)(?:\n|\s|$)'
            col_matches = re.finditer(col_pattern, class_body, re.DOTALL)

            for cm in col_matches:
                col_name = cm.group(1)
                col_args = cm.group(2).strip()
                col_args = ' '.join(col_args.split())  # normalize whitespace
                columns.append({
                    'name': col_name,
                    'args': col_args
                })

            tables.append({
                'name': class_name,
                'tablename': tablename,
                'columns': columns
            })

        return tables

    def _generate_alembic_migration_content(self, tables: List[Dict]) -> str:
        """Generate Alembic migration file content with real op.create_table() calls."""

        revision_id = self._generate_revision_id()
        table_names = ', '.join(t['tablename'] for t in tables)

        # Generate upgrade operations
        upgrade_ops = []
        downgrade_ops = []

        for table in tables:
            tablename = table['tablename']
            columns = table.get('columns', [])

            # Build column definitions
            col_defs = ["        sa.Column('id', sa.Integer(), nullable=False),"]

            for col in columns:
                col_name = col['name']
                col_args = col['args']
                col_defs.append(f"        sa.Column('{col_name}', {col_args}),")

            col_defs_str = '\n'.join(col_defs)

            # Upgrade operation
            upgrade_ops.append(f"""    op.create_table(
        '{tablename}',
{col_defs_str}
        sa.PrimaryKeyConstraint('id')
    )""")

            # Downgrade operation
            downgrade_ops.append(f"    op.drop_table('{tablename}')")

        upgrade_str = '\n'.join(upgrade_ops)
        downgrade_str = '\n'.join(downgrade_ops)

        content = f'''"""Auto-generated migration for tables: {table_names}

Revision ID: {revision_id}
Revises:
Create Date: {datetime.datetime.now().isoformat()}

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '{revision_id}'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
{upgrade_str}


def downgrade():
{downgrade_str}
'''

        return content

    def _extract_spring_entities(self, code: str) -> List[Dict]:
        """Extract Spring @Entity definitions with full field extraction."""
        entities = []

        # Find @Entity class blocks
        pattern = r'@Entity.*?public\s+class\s+(\w+)\s*\{(.*?)\n}'
        matches = re.finditer(pattern, code, re.DOTALL)

        for match in matches:
            entity_name = match.group(1)
            class_body = match.group(2)
            tablename = self._camel_to_snake(entity_name)

            # Extract fields with @Column annotations
            fields = []
            field_pattern = r'@Column.*?private\s+(\w+)\s+(\w+);'
            field_matches = re.finditer(field_pattern, class_body, re.DOTALL)

            for fm in field_matches:
                field_type = fm.group(1)
                field_name = fm.group(2)
                sql_type = self._java_to_sql_type(field_type)
                fields.append({
                    'name': field_name,
                    'type': sql_type
                })

            entities.append({
                'name': entity_name,
                'tablename': tablename,
                'fields': fields
            })

        return entities

    def _generate_flyway_sql(self, entities: List[Dict], feature_name: str) -> str:
        """Generate Flyway SQL migration with full schema."""

        sql_lines = [
            "-- Flyway migration",
            f"-- Feature: {feature_name}",
            "",
        ]

        for entity in entities:
            table_name = entity['tablename']
            fields = entity.get('fields', [])

            sql_lines.append(f"CREATE TABLE {table_name} (")
            sql_lines.append("    id BIGINT PRIMARY KEY AUTO_INCREMENT,")

            for field in fields:
                field_name = field['name']
                field_type = field['type']
                sql_lines.append(f"    {field_name} {field_type},")

            sql_lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
            sql_lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
            sql_lines.append(");")
            sql_lines.append("")

        return "\n".join(sql_lines)

    def _extract_go_tables(self, code: str) -> List[Dict]:
        """Extract Go struct definitions with full field extraction."""
        structs = []

        # Find struct definitions with fields
        pattern = r'type\s+(\w+)\s+struct\s*\{(.*?)\n\}'
        matches = re.finditer(pattern, code, re.DOTALL)

        for match in matches:
            struct_name = match.group(1)
            struct_body = match.group(2)
            tablename = self._camel_to_snake(struct_name)

            # Extract fields
            fields = []
            field_pattern = r'(\w+)\s+(\w+)\s+`'
            field_matches = re.finditer(field_pattern, struct_body)

            for fm in field_matches:
                field_name = fm.group(1)
                field_type = fm.group(2)
                sql_type = self._go_to_sql_type(field_type)
                fields.append({
                    'name': self._camel_to_snake(field_name),
                    'type': sql_type
                })

            structs.append({
                'name': struct_name,
                'tablename': tablename,
                'fields': fields
            })

        return structs

    def _generate_go_migration_sql(self, tables: List[Dict]) -> str:
        """Generate SQL migration for Go with full schema."""

        sql_lines = [
            "-- Go migration (golang-migrate)",
            "",
        ]

        for table in tables:
            tablename = table['tablename']
            fields = table.get('fields', [])

            sql_lines.append(f"CREATE TABLE {tablename} (")
            sql_lines.append("    id SERIAL PRIMARY KEY,")

            for field in fields:
                field_name = field['name']
                field_type = field['type']
                sql_lines.append(f"    {field_name} {field_type},")

            sql_lines.append("    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,")
            sql_lines.append("    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            sql_lines.append(");")
            sql_lines.append("")

        return "\n".join(sql_lines)

    def _camel_to_snake(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def _generate_revision_id(self) -> str:
        """Generate random Alembic revision ID."""
        random_hash = hashlib.md5(self.timestamp.encode()).hexdigest()[:12]
        return random_hash

    def _java_to_sql_type(self, java_type: str) -> str:
        """Map Java types to SQL types."""
        type_map = {
            'String': 'VARCHAR(255)',
            'Integer': 'INT',
            'Long': 'BIGINT',
            'Double': 'DECIMAL(10,2)',
            'Boolean': 'BOOLEAN',
            'LocalDateTime': 'DATETIME',
            'LocalDate': 'DATE',
            'BigDecimal': 'DECIMAL(19,2)',
        }
        return type_map.get(java_type, 'VARCHAR(255)')

    def _go_to_sql_type(self, go_type: str) -> str:
        """Map Go types to SQL types."""
        type_map = {
            'string': 'VARCHAR(255)',
            'int': 'INT',
            'int64': 'BIGINT',
            'float64': 'DECIMAL(10,2)',
            'bool': 'BOOLEAN',
            'time.Time': 'DATETIME',
            'decimal.Decimal': 'DECIMAL(19,2)',
        }
        return type_map.get(go_type, 'VARCHAR(255)')


def main():
    """CLI entry point for migration generation."""
    parser = argparse.ArgumentParser(
        description='Generate database migrations for new models'
    )
    parser.add_argument(
        '--framework',
        required=True,
        choices=['django', 'fastapi', 'spring', 'go'],
        help='Target framework'
    )
    parser.add_argument(
        '--project-root',
        required=True,
        help='Path to project root'
    )
    parser.add_argument(
        '--feature-name',
        required=True,
        help='Feature name for migration (e.g., "User Auth")'
    )
    parser.add_argument(
        '--models-file',
        required=True,
        help='Path to file containing model definitions'
    )

    args = parser.parse_args()

    with timed_run("generate_migrations") as timer:
        logger.debug(f"Generating {args.framework} migration for {args.feature_name}")

        # Read models file
        try:
            with open(args.models_file, 'r') as f:
                models_code = f.read()
        except FileNotFoundError:
            logger.error(f"Models file not found: {args.models_file}")
            return 1

        # Generate migration
        gen = MigrationGenerator(args.framework, args.project_root)
        filepath, content = gen.generate_migration(models_code, args.feature_name)

        if not filepath:
            logger.error(f"Unsupported framework: {args.framework}")
            return 1

        logger.debug(f"Generated migration: {filepath}")
        print(f"Migration file: {filepath}\n")
        print(content)

        check_budget("generate_migrations", timer.elapsed_ms, logger)

    logger.debug(f"generate_migrations completed in {timer.elapsed_ms:.0f}ms")
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main())
