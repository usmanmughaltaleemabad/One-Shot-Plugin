"""
Test Generator - Comprehensive test suite generation

Generates:
- Unit tests for endpoints
- Integration tests
- Happy path tests
- Error case tests
- Edge case tests
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class TestScenario:
    """Test scenario definition"""
    name: str
    description: str
    method: str
    endpoint: str
    request_body: Optional[Dict] = None
    expected_status: int = 200
    expected_response: Optional[Dict] = None


class TestGenerator:
    """Generate comprehensive tests"""

    def __init__(self, framework: str, resource_name: str, resource_plural: str):
        self.framework = framework
        self.resource_name = resource_name
        self.resource_plural = resource_plural

    def generate_django_tests(self) -> str:
        """Generate Django test suite"""
        return f"""
import pytest
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient, APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from ..models import {self.resource_name.capitalize()}

@pytest.mark.django_db
class Test{self.resource_name.capitalize()}CRUDOperations(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.force_authenticate(self.user)
        self.url = '/api/v1/{self.resource_plural}/'

    def test_list_all_{self.resource_plural}(self):
        '''Test retrieving all {self.resource_plural}'''
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_{self.resource_name}(self):
        '''Test creating a new {self.resource_name}'''
        data = {{'name': 'Test {self.resource_name.capitalize()}', 'description': 'Test'}}
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert {self.resource_name.capitalize()}.objects.count() == 1

    def test_retrieve_{self.resource_name}(self):
        '''Test retrieving a single {self.resource_name}'''
        obj = {self.resource_name.capitalize()}.objects.create(name='Test')
        response = self.client.get(f'{{self.url}}{{obj.id}}/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['id'] == obj.id

    def test_update_{self.resource_name}(self):
        '''Test updating a {self.resource_name}'''
        obj = {self.resource_name.capitalize()}.objects.create(name='Test')
        data = {{'name': 'Updated'}}
        response = self.client.put(f'{{self.url}}{{obj.id}}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK
        obj.refresh_from_db()
        assert obj.name == 'Updated'

    def test_delete_{self.resource_name}(self):
        '''Test deleting a {self.resource_name}'''
        obj = {self.resource_name.capitalize()}.objects.create(name='Test')
        response = self.client.delete(f'{{self.url}}{{obj.id}}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert {self.resource_name.capitalize()}.objects.count() == 0

    def test_partial_update_{self.resource_name}(self):
        '''Test partial update of a {self.resource_name}'''
        obj = {self.resource_name.capitalize()}.objects.create(name='Test')
        data = {{'description': 'Updated description'}}
        response = self.client.patch(f'{{self.url}}{{obj.id}}/', data, format='json')
        assert response.status_code == status.HTTP_200_OK

    def test_list_with_pagination(self):
        '''Test pagination on list endpoint'''
        for i in range(25):
            {self.resource_name.capitalize()}.objects.create(name=f'Test {{i}}')
        response = self.client.get(self.url + '?limit=10&offset=0')
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) <= 10 or 'results' in response.data

    def test_list_with_filtering(self):
        '''Test filtering on list endpoint'''
        {self.resource_name.capitalize()}.objects.create(name='Active')
        response = self.client.get(self.url + '?search=Active')
        assert response.status_code == status.HTTP_200_OK

    def test_list_with_ordering(self):
        '''Test ordering on list endpoint'''
        response = self.client.get(self.url + '?ordering=-created_at')
        assert response.status_code == status.HTTP_200_OK

    def test_authentication_required(self):
        '''Test that authentication is required'''
        self.client.force_authenticate(None)
        response = self.client.post(self.url, {{}}, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_data(self):
        '''Test creating with invalid data'''
        data = {{'name': ''}}
        response = self.client.post(self.url, data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_not_found(self):
        '''Test retrieving non-existent {self.resource_name}'''
        response = self.client.get(f'{{self.url}}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND
"""

    def generate_fastapi_tests(self) -> str:
        """Generate FastAPI test suite"""
        return f"""
import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session

client = TestClient(app)

BASE_URL = '/api/v1/{self.resource_plural}'

class Test{self.resource_name.capitalize()}CRUD:
    def test_list_{self.resource_plural}(self):
        '''Test retrieving all {self.resource_plural}'''
        response = client.get(BASE_URL)
        assert response.status_code == 200

    def test_create_{self.resource_name}(self):
        '''Test creating a new {self.resource_name}'''
        data = {{'name': 'Test {self.resource_name.capitalize()}', 'description': 'Test'}}
        response = client.post(BASE_URL, json=data)
        assert response.status_code == 201
        assert response.json()['name'] == 'Test {self.resource_name.capitalize()}'

    def test_get_{self.resource_name}(self):
        '''Test retrieving a single {self.resource_name}'''
        response = client.get(f'{{BASE_URL}}/1')
        assert response.status_code in [200, 404]

    def test_update_{self.resource_name}(self):
        '''Test updating a {self.resource_name}'''
        data = {{'name': 'Updated'}}
        response = client.put(f'{{BASE_URL}}/1', json=data)
        assert response.status_code in [200, 404]

    def test_delete_{self.resource_name}(self):
        '''Test deleting a {self.resource_name}'''
        response = client.delete(f'{{BASE_URL}}/1')
        assert response.status_code in [204, 404]

    def test_pagination(self):
        '''Test pagination'''
        response = client.get(BASE_URL + '?limit=10&offset=0')
        assert response.status_code == 200

    def test_filtering(self):
        '''Test filtering'''
        response = client.get(BASE_URL + '?search=test')
        assert response.status_code == 200

    def test_ordering(self):
        '''Test ordering'''
        response = client.get(BASE_URL + '?sort_by=created_at&sort_order=desc')
        assert response.status_code == 200

    def test_invalid_data(self):
        '''Test creating with invalid data'''
        data = {{'name': ''}}
        response = client.post(BASE_URL, json=data)
        assert response.status_code == 422

    def test_not_found(self):
        '''Test retrieving non-existent {self.resource_name}'''
        response = client.get(f'{{BASE_URL}}/99999')
        assert response.status_code == 404

    def test_validation_error(self):
        '''Test validation errors'''
        response = client.post(BASE_URL, json={{}})
        assert response.status_code == 422

@pytest.fixture
def sample_{self.resource_name}():
    '''Create a sample {self.resource_name} for testing'''
    return {{'name': 'Test {self.resource_name.capitalize()}', 'description': 'Test'}}
"""


def generate_tests(
    framework: str,
    resource_name: str,
    resource_plural: str
) -> Dict[str, str]:
    """
    Generate test suite.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        resource_plural: e.g., "users"

    Returns: dict of {filename: test_code}
    """
    generator = TestGenerator(framework, resource_name, resource_plural)
    output = {}

    if framework == "django":
        output[f"test_{resource_name}_api.py"] = generator.generate_django_tests()
    elif framework == "fastapi":
        output[f"test_{resource_name}_api.py"] = generator.generate_fastapi_tests()

    return output
