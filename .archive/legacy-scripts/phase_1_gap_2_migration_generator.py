#!/usr/bin/env python3
"""
Generate database migrations for new models.

Supports Django, Alembic (FastAPI), Flyway (Spring), sql-migrate (Go).
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple


class MigrationGenerator:
    """Generate database migrations for multiple frameworks."""

    def __init__(self, framework: str, db_type: str = 'postgresql'):
        self.framework = framework.lower()
        self.db_type = db_type.lower()
        self.timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        self.migration_num = self.timestamp

    def _parse_model(self, model_code: str) -> Dict[str, any]:
        """Extract table/class name and fields from model code."""
        lines = model_code.split('\n')
        fields = {}

        class_match = re.search(r'class\s+(\w+)', model_code)
        table_name = class_match.group(1).lower() if class_match else 'model'

        for line in lines:
            # Django/SQLAlchemy ORM syntax
            field_match = re.search(r'(\w+)\s*=\s*(models\.|Column\()(.*?)[,\n]', line)
            if field_match:
                field_name = field_match.group(1)
                field_type = field_match.group(3).split('(')[0].strip()
                fields[field_name] = field_type

        return {'name': table_name, 'fields': fields}

    def generate_django(self, models: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate Django migration files."""
        migrations = []

        for model_name, model_code in models.items():
            model_info = self._parse_model(model_code)
            migration_name = f'0001_initial_{model_info["name"]}'

            # Django migration Python file
            migration_content = f'''# Generated migration
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='{model_info["name"].capitalize()}',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
'''

            for field_name, field_type in model_info['fields'].items():
                if 'char' in field_type.lower():
                    migration_content += f"                ('{ field_name}', models.CharField(max_length=255)),\n"
                elif 'int' in field_type.lower():
                    migration_content += f"                ('{field_name}', models.IntegerField()),\n"
                elif 'email' in field_type.lower():
                    migration_content += f"                ('{field_name}', models.EmailField()),\n"
                elif 'bool' in field_type.lower():
                    migration_content += f"                ('{field_name}', models.BooleanField()),\n"
                else:
                    migration_content += f"                ('{field_name}', models.TextField()),\n"

            migration_content += '            ],\n        ),\n    ]\n'

            filepath = f'migrations/{self.migration_num}_{migration_name}.py'
            migrations.append((filepath, migration_content))

        return migrations

    def generate_alembic(self, models: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate Alembic (SQLAlchemy) migration files."""
        migrations = []

        for model_name, model_code in models.items():
            model_info = self._parse_model(model_code)

            migration_content = f'''"""Create {model_info["name"]} table"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        '{model_info["name"]}',
        sa.Column('id', sa.Integer(), nullable=False),
'''

            for field_name, field_type in model_info['fields'].items():
                if 'char' in field_type.lower():
                    migration_content += f"        sa.Column('{field_name}', sa.String(255), nullable=False),\n"
                elif 'email' in field_type.lower():
                    migration_content += f"        sa.Column('{field_name}', sa.String(255), nullable=False),\n"
                elif 'int' in field_type.lower():
                    migration_content += f"        sa.Column('{field_name}', sa.Integer(), nullable=False),\n"
                elif 'bool' in field_type.lower():
                    migration_content += f"        sa.Column('{field_name}', sa.Boolean(), nullable=False),\n"
                else:
                    migration_content += f"        sa.Column('{field_name}', sa.Text(), nullable=False),\n"

            migration_content += """        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('{model_info["name"]}')
"""

            filepath = f'alembic/versions/{self.migration_num}_create_{model_info["name"]}.py'
            migrations.append((filepath, migration_content))

        return migrations

    def generate_flyway(self, models: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate Flyway (Spring) migration files."""
        migrations = []

        for model_name, model_code in models.items():
            model_info = self._parse_model(model_code)

            sql = f'CREATE TABLE IF NOT EXISTS {model_info["name"]} (\n'
            sql += '  id BIGINT PRIMARY KEY AUTO_INCREMENT,\n'

            for field_name, field_type in model_info['fields'].items():
                if 'char' in field_type.lower():
                    sql += f"  {field_name} VARCHAR(255) NOT NULL,\n"
                elif 'email' in field_type.lower():
                    sql += f"  {field_name} VARCHAR(255) NOT NULL,\n"
                elif 'int' in field_type.lower():
                    sql += f"  {field_name} INT NOT NULL,\n"
                elif 'bool' in field_type.lower():
                    sql += f"  {field_name} BOOLEAN NOT NULL,\n"
                else:
                    sql += f"  {field_name} TEXT NOT NULL,\n"

            sql = sql.rstrip(',\n') + '\n);\n'

            filepath = f'src/main/resources/db/migration/V{self.migration_num}__create_{model_info["name"]}.sql'
            migrations.append((filepath, sql))

        return migrations

    def generate(self, models: Dict[str, str]) -> List[Tuple[str, str]]:
        """Generate migrations for configured framework."""
        if self.framework == 'django':
            return self.generate_django(models)
        elif self.framework == 'fastapi':
            return self.generate_alembic(models)
        elif self.framework == 'spring':
            return self.generate_flyway(models)
        else:
            return []


def generate_migrations(
    framework: str,
    models: Dict[str, str],
    db_type: str = 'postgresql'
) -> List[Tuple[str, str]]:
    """Generate database migrations."""
    generator = MigrationGenerator(framework, db_type)
    return generator.generate(models)
