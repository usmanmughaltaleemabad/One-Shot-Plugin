"""
Migration Generator - Database migration generation

Generates:
- Django migrations
- Alembic migrations (SQLAlchemy)
- Flyway migrations (Spring/Java)
- Golang migrate migrations
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class MigrationField:
    """Migration field definition"""
    name: str
    field_type: str
    nullable: bool = False
    unique: bool = False
    primary_key: bool = False
    default: Optional[str] = None


class MigrationGenerator:
    """Generate database migrations"""

    def __init__(self, framework: str, language: str):
        self.framework = framework
        self.language = language

    def generate_django_migration(self, resource_name: str, fields: List[MigrationField]) -> str:
        """Generate Django migration file"""
        field_definitions = []

        for field in fields:
            if field.primary_key:
                field_definitions.append(f"    ('{field.name}', models.AutoField(primary_key=True)),")
            else:
                field_type = self._get_django_field_type(field.field_type)
                null_param = f", null={field.nullable}" if field.nullable else ""
                unique_param = f", unique={field.unique}" if field.unique else ""
                default_param = f", default={field.default}" if field.default else ""
                field_definitions.append(f"    ('{field.name}', {field_type}({null_param}{unique_param}{default_param})),")

        return f"""# Generated migration for {resource_name}

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='{resource_name.capitalize()}',
            fields=[
{''.join(field_definitions)}
            ],
        ),
    ]
"""

    def generate_alembic_migration(self, resource_name: str, fields: List[MigrationField]) -> str:
        """Generate Alembic migration (SQLAlchemy)"""
        table_name = resource_name.lower() + "s"
        column_definitions = []

        for field in fields:
            col_type = self._get_sqlalchemy_type(field.field_type)
            nullable = f"nullable={field.nullable}" if field.nullable else "nullable=False"
            unique = f", unique={field.unique}" if field.unique else ""
            primary_key = ", primary_key=True" if field.primary_key else ""
            column_definitions.append(f"    sa.Column('{field.name}', {col_type}, {nullable}{primary_key}{unique}),")

        return f"""\"\"\"Create {resource_name} table

Revision ID: auto_generated
Revises:
Create Date: 2026-05-08 00:00:00.000000

\"\"\"
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'auto_generated'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        '{table_name}',
{''.join(column_definitions)}
    )

def downgrade():
    op.drop_table('{table_name}')
"""

    def generate_flyway_migration(self, resource_name: str, fields: List[MigrationField]) -> str:
        """Generate Flyway migration (Spring/Java)"""
        table_name = resource_name.lower() + "s"
        column_definitions = []

        for field in fields:
            col_type = self._get_sql_type(field.field_type)
            nullable = "" if field.nullable else " NOT NULL"
            unique = " UNIQUE" if field.unique else ""
            primary_key = " PRIMARY KEY" if field.primary_key else ""
            column_definitions.append(f"  {field.name} {col_type}{nullable}{unique}{primary_key},")

        # Remove trailing comma from last column
        if column_definitions:
            column_definitions[-1] = column_definitions[-1].rstrip(',') + ','

        return f"""-- Create {resource_name} table

CREATE TABLE {table_name} (
{''.join(column_definitions)}
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_{table_name}_created_at ON {table_name}(created_at);
"""

    def generate_golang_migrate(self, resource_name: str, fields: List[MigrationField]) -> str:
        """Generate golang-migrate migration"""
        table_name = resource_name.lower() + "s"
        column_definitions = []

        for field in fields:
            col_type = self._get_sql_type(field.field_type)
            nullable = "" if field.nullable else " NOT NULL"
            unique = " UNIQUE" if field.unique else ""
            primary_key = " PRIMARY KEY" if field.primary_key else ""
            column_definitions.append(f"  {field.name} {col_type}{nullable}{unique}{primary_key},")

        if column_definitions:
            column_definitions[-1] = column_definitions[-1].rstrip(',') + ','

        return f"""-- +migrate Up
CREATE TABLE {table_name} (
{''.join(column_definitions)}
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE INDEX idx_{table_name}_created_at ON {table_name}(created_at);

-- +migrate Down
DROP TABLE IF EXISTS {table_name};
"""

    @staticmethod
    def _get_django_field_type(field_type: str) -> str:
        type_map = {
            "string": "models.CharField(max_length=255)",
            "text": "models.TextField()",
            "integer": "models.IntegerField()",
            "boolean": "models.BooleanField()",
            "datetime": "models.DateTimeField()",
            "date": "models.DateField()",
            "decimal": "models.DecimalField(max_digits=10, decimal_places=2)",
            "json": "models.JSONField()"
        }
        return type_map.get(field_type, "models.CharField(max_length=255)")

    @staticmethod
    def _get_sqlalchemy_type(field_type: str) -> str:
        type_map = {
            "string": "sa.String(255)",
            "text": "sa.Text()",
            "integer": "sa.Integer()",
            "boolean": "sa.Boolean()",
            "datetime": "sa.DateTime()",
            "date": "sa.Date()",
            "decimal": "sa.Numeric(10, 2)",
            "json": "sa.JSON()"
        }
        return type_map.get(field_type, "sa.String(255)")

    @staticmethod
    def _get_sql_type(field_type: str) -> str:
        type_map = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INT",
            "boolean": "BOOLEAN",
            "datetime": "DATETIME",
            "date": "DATE",
            "decimal": "DECIMAL(10,2)",
            "json": "JSON"
        }
        return type_map.get(field_type, "VARCHAR(255)")


def generate_migrations(
    framework: str,
    language: str,
    resource_name: str,
    fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate migrations.

    Args:
        framework: django, spring, go
        language: python, java, go
        resource_name: e.g., "user"
        fields: list of field definitions

    Returns: dict of {filename: migration_content}
    """
    generator = MigrationGenerator(framework, language)

    field_objs = [
        MigrationField(
            name=f.get("name"),
            field_type=f.get("type", "string"),
            nullable=f.get("nullable", False),
            unique=f.get("unique", False),
            primary_key=f.get("primary_key", False),
            default=f.get("default")
        )
        for f in (fields or [])
    ]

    output = {}

    if framework == "django":
        filename = "0001_initial.py"
        output[filename] = generator.generate_django_migration(resource_name, field_objs)
    elif framework == "spring" or language == "java":
        filename = f"V1__{resource_name.capitalize()}_Create.sql"
        output[filename] = generator.generate_flyway_migration(resource_name, field_objs)
    elif framework == "go" or language == "go":
        filename = f"000001_{resource_name}_create.up.sql"
        output[filename] = generator.generate_golang_migrate(resource_name, field_objs)

    return output
