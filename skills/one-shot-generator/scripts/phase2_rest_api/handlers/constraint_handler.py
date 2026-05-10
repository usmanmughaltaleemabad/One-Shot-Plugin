"""
Constraint Handler - Database constraints and validation

Generates:
- Foreign key constraints
- Unique constraints
- Check constraints
- NOT NULL constraints
- Default value constraints
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ConstraintType(Enum):
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    CHECK = "check"
    NOT_NULL = "not_null"
    DEFAULT = "default"
    PRIMARY_KEY = "primary_key"


@dataclass
class Constraint:
    """Database constraint definition"""
    name: str
    constraint_type: ConstraintType
    column: str
    referenced_table: Optional[str] = None
    referenced_column: Optional[str] = None
    check_expression: Optional[str] = None
    default_value: Optional[Any] = None
    on_delete: str = "CASCADE"
    on_update: str = "CASCADE"


class ConstraintHandler:
    """Generate database constraints"""

    def __init__(self, framework: str):
        self.framework = framework

    def generate_django_constraints(self, constraints: List[Constraint]) -> str:
        """Generate Django model constraints"""
        constraint_code = []

        for constraint in constraints:
            if constraint.constraint_type == ConstraintType.UNIQUE:
                constraint_code.append(f"        models.UniqueConstraint(fields=['{constraint.column}'], name='{constraint.name}'),")

            elif constraint.constraint_type == ConstraintType.CHECK:
                constraint_code.append(
                    f"        models.CheckConstraint(check=models.Q({constraint.check_expression}), name='{constraint.name}'),"
                )

            elif constraint.constraint_type == ConstraintType.FOREIGN_KEY:
                constraint_code.append(
                    f"        models.ForeignKey('{constraint.referenced_table}', on_delete=models.{constraint.on_delete.upper()}),"
                )

        return f"""
from django.db import models

class Meta:
    constraints = [
{''.join(constraint_code) if constraint_code else '        # Add constraints here'}
    ]
"""

    def generate_sqlalchemy_constraints(self, constraints: List[Constraint]) -> str:
        """Generate SQLAlchemy constraints"""
        constraint_code = []

        for constraint in constraints:
            if constraint.constraint_type == ConstraintType.UNIQUE:
                constraint_code.append(f"        UniqueConstraint('{constraint.column}', name='{constraint.name}'),")

            elif constraint.constraint_type == ConstraintType.CHECK:
                constraint_code.append(f"        CheckConstraint('{constraint.check_expression}', name='{constraint.name}'),")

            elif constraint.constraint_type == ConstraintType.FOREIGN_KEY:
                constraint_code.append(
                    f"        ForeignKeyConstraint(['{constraint.column}'], ['{constraint.referenced_table}.{constraint.referenced_column}'], "
                    f"ondelete='{constraint.on_delete}', onupdate='{constraint.on_update}'),\n"
                )

        return f"""
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    age = Column(Integer)
    status = Column(String(50), default='active')

    __table_args__ = (
{''.join(constraint_code) if constraint_code else '        # Add constraints here'}
    )
"""

    def generate_sql_constraints(self, constraints: List[Constraint]) -> str:
        """Generate raw SQL constraints"""
        constraint_sql = []

        for constraint in constraints:
            if constraint.constraint_type == ConstraintType.UNIQUE:
                constraint_sql.append(f"ALTER TABLE users ADD CONSTRAINT {constraint.name} UNIQUE ({constraint.column});")

            elif constraint.constraint_type == ConstraintType.CHECK:
                constraint_sql.append(
                    f"ALTER TABLE users ADD CONSTRAINT {constraint.name} CHECK ({constraint.check_expression});"
                )

            elif constraint.constraint_type == ConstraintType.FOREIGN_KEY:
                constraint_sql.append(
                    f"ALTER TABLE users ADD CONSTRAINT {constraint.name} FOREIGN KEY ({constraint.column}) "
                    f"REFERENCES {constraint.referenced_table}({constraint.referenced_column}) "
                    f"ON DELETE {constraint.on_delete} ON UPDATE {constraint.on_update};"
                )

        return """
-- Unique constraints
ALTER TABLE users ADD CONSTRAINT uk_email UNIQUE (email);

-- Check constraints
ALTER TABLE users ADD CONSTRAINT ck_age CHECK (age >= 0 AND age <= 150);
ALTER TABLE users ADD CONSTRAINT ck_status CHECK (status IN ('active', 'inactive', 'suspended'));

-- Foreign key constraints
ALTER TABLE orders ADD CONSTRAINT fk_orders_user FOREIGN KEY (user_id)
  REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE;

-- Primary key
ALTER TABLE users ADD PRIMARY KEY (id);

-- Not null constraints
ALTER TABLE users MODIFY COLUMN email VARCHAR(255) NOT NULL;

-- Default values
ALTER TABLE users MODIFY COLUMN status VARCHAR(50) DEFAULT 'active';
ALTER TABLE users MODIFY COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
"""

    def generate_constraint_validation(self) -> str:
        """Generate constraint validation helpers"""
        return """
class ConstraintValidator:
    '''Validate data against constraints'''

    @staticmethod
    def validate_unique(table, column, value):
        '''Check if value already exists for unique column'''
        return not table.objects.filter(**{column: value}).exists()

    @staticmethod
    def validate_foreign_key(table, column, ref_table, ref_id):
        '''Check if referenced record exists'''
        try:
            ref_table.objects.get(pk=ref_id)
            return True
        except ref_table.DoesNotExist:
            return False

    @staticmethod
    def validate_check(value, check_expression):
        '''Evaluate check constraint expression'''
        return eval(check_expression, {'value': value})

    @staticmethod
    def validate_not_null(value):
        '''Check if value is not null'''
        return value is not None

    @staticmethod
    def enforce_constraints(data: dict, schema):
        '''Enforce all constraints on data'''
        errors = []

        for field_name, field_config in schema.items():
            value = data.get(field_name)

            if field_config.get('not_null', False) and not ConstraintValidator.validate_not_null(value):
                errors.append(f'{field_name} cannot be null')

            if field_config.get('unique', False):
                if not ConstraintValidator.validate_unique(field_name, value):
                    errors.append(f'{field_name} must be unique')

            if field_config.get('check'):
                if not ConstraintValidator.validate_check(value, field_config['check']):
                    errors.append(f'{field_name} failed check constraint')

        return errors
"""


def generate_constraints(
    framework: str,
    constraints: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, str]:
    """
    Generate constraint code.

    Args:
        framework: django, fastapi, spring, go
        constraints: list of constraint definitions

    Returns: dict of {filename: code_content}
    """
    handler = ConstraintHandler(framework)

    constraint_objs = [
        Constraint(
            name=c.get("name"),
            constraint_type=ConstraintType(c.get("type", "unique")),
            column=c.get("column"),
            referenced_table=c.get("referenced_table"),
            referenced_column=c.get("referenced_column"),
            check_expression=c.get("check_expression"),
            default_value=c.get("default_value"),
            on_delete=c.get("on_delete", "CASCADE"),
            on_update=c.get("on_update", "CASCADE")
        )
        for c in (constraints or [])
    ]

    output = {}

    if framework == "django":
        output["constraints.py"] = handler.generate_django_constraints(constraint_objs)
    else:
        output["constraints.py"] = handler.generate_sqlalchemy_constraints(constraint_objs)

    output["constraints.sql"] = handler.generate_sql_constraints(constraint_objs)
    output["constraint_validator.py"] = handler.generate_constraint_validation()

    return output
