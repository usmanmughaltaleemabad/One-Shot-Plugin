"""
Fixtures Generator - Test fixtures and factories

Generates:
- Factory Boy factories for test data
- Pytest fixtures
- Fixture data sets
- Seed data for testing
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


class FixturesGenerator:
    """Generate test fixtures"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_factory(self) -> str:
        """Generate Factory Boy factory"""
        return f"""
import factory
from faker import Faker
from ..models import {self.resource_name.capitalize()}

fake = Faker()

class {self.resource_name.capitalize()}Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = {self.resource_name.capitalize()}

    name = factory.LazyFunction(lambda: fake.name())
    description = factory.LazyFunction(lambda: fake.text(max_nb_chars=200))
    email = factory.LazyFunction(lambda: fake.email())
    created_at = factory.LazyFunction(lambda: fake.date_time_this_year())
    updated_at = factory.LazyFunction(lambda: fake.date_time_this_year())

    @factory.post_generation
    def tags(obj, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            for tag in extracted:
                obj.tags.add(tag)
"""

    def generate_pytest_fixtures(self) -> str:
        """Generate pytest fixtures"""
        return f"""
import pytest
from django.test import Client
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    '''Return API client'''
    return APIClient()

@pytest.fixture
def authenticated_user():
    '''Create an authenticated test user'''
    return User.objects.create_user('testuser', 'test@example.com', 'password')

@pytest.fixture
def authenticated_client(authenticated_user):
    '''Return authenticated API client'''
    client = APIClient()
    client.force_authenticate(authenticated_user)
    return client

@pytest.fixture
def {self.resource_name}_data():
    '''Sample {self.resource_name} data'''
    return {{
        'name': 'Test {self.resource_name.capitalize()}',
        'description': 'Test description',
        'email': 'test@example.com',
    }}

@pytest.fixture
def {self.resource_name}_factory():
    '''Factory for creating {self.resource_name} objects'''
    from .factories import {self.resource_name.capitalize()}Factory
    return {self.resource_name.capitalize()}Factory

@pytest.fixture
def multiple_{self.resource_plural}(db, {self.resource_name}_factory):
    '''Create multiple {self.resource_plural} for testing'''
    return {self.resource_name}_factory.create_batch(5)
"""

    def generate_conftest(self) -> str:
        """Generate conftest.py for shared fixtures"""
        return f"""
import os
import django
from django.conf import settings

def pytest_configure():
    '''Configure pytest for Django tests'''
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

pytest_plugins = ['pytest_django']

import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture(scope='session')
def django_db_setup():
    '''Set up Django test database'''
    settings.DATABASES['default'] = {{
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }}

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user_factory():
    '''Factory for creating users'''
    def _create_user(username='testuser', password='testpass'):
        return User.objects.create_user(username, 'test@example.com', password)
    return _create_user

@pytest.fixture
def authenticated_client(user_factory):
    client = APIClient()
    user = user_factory()
    client.force_authenticate(user)
    return client
"""

    def generate_seed_data(self) -> str:
        """Generate seed data for testing"""
        return f"""
import json

SEED_DATA = {{
    '{self.resource_plural}': [
        {{
            'id': 1,
            'name': '{self.resource_name.capitalize()} 1',
            'description': 'First {self.resource_name}',
            'email': '{self.resource_name}1@example.com',
            'created_at': '2026-01-01T00:00:00Z',
            'updated_at': '2026-01-01T00:00:00Z'
        }},
        {{
            'id': 2,
            'name': '{self.resource_name.capitalize()} 2',
            'description': 'Second {self.resource_name}',
            'email': '{self.resource_name}2@example.com',
            'created_at': '2026-01-02T00:00:00Z',
            'updated_at': '2026-01-02T00:00:00Z'
        }},
        {{
            'id': 3,
            'name': '{self.resource_name.capitalize()} 3',
            'description': 'Third {self.resource_name}',
            'email': '{self.resource_name}3@example.com',
            'created_at': '2026-01-03T00:00:00Z',
            'updated_at': '2026-01-03T00:00:00Z'
        }},
    ]
}}

class SeedDataLoader:
    @staticmethod
    def load_seed_data():
        '''Load seed data for testing'''
        return SEED_DATA

    @staticmethod
    def get_{self.resource_plural}():
        '''Get all seed {self.resource_plural}'''
        return SEED_DATA['{self.resource_plural}']

    @staticmethod
    def get_{self.resource_name}(id: int):
        '''Get seed {self.resource_name} by id'''
        for item in SEED_DATA['{self.resource_plural}']:
            if item['id'] == id:
                return item
        return None

    @staticmethod
    def save_seed_data(filepath: str):
        '''Save seed data to JSON file'''
        with open(filepath, 'w') as f:
            json.dump(SEED_DATA, f, indent=2)

    @staticmethod
    def load_from_file(filepath: str):
        '''Load seed data from JSON file'''
        with open(filepath, 'r') as f:
            return json.load(f)
"""


def generate_fixtures(framework: str, resource_name: str) -> Dict[str, str]:
    """
    Generate test fixtures.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"

    Returns: dict of {filename: fixture_code}
    """
    generator = FixturesGenerator(framework, resource_name)
    output = {}

    if framework == "django":
        output["factories.py"] = generator.generate_factory()
        output["conftest.py"] = generator.generate_conftest()

    output["fixtures.py"] = generator.generate_pytest_fixtures()
    output["seed_data.py"] = generator.generate_seed_data()

    return output
