"""
Integration Test Generator - Integration test scenarios

Generates:
- End-to-end flow tests
- Multi-endpoint integration tests
- Database transaction tests
- Error scenario tests
"""

from typing import Dict, Any, List, Optional


class IntegrationTestGenerator:
    """Generate integration tests"""

    def __init__(self, framework: str, resource_name: str, resource_plural: str):
        self.framework = framework
        self.resource_name = resource_name
        self.resource_plural = resource_plural

    def generate_django_integration_tests(self) -> str:
        """Generate Django integration tests"""
        return f"""
import pytest
from django.test import TransactionTestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from ..models import {self.resource_name.capitalize()}

@pytest.mark.django_db(transaction=True)
class Test{self.resource_name.capitalize()}IntegrationScenarios(TransactionTestCase):
    '''Integration tests for {self.resource_name} workflows'''

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.client.force_authenticate(self.user)
        self.base_url = '/api/v1/{self.resource_plural}/'

    def test_full_crud_workflow(self):
        '''Test complete CRUD workflow'''
        # Create
        create_data = {{'name': 'Integration Test', 'description': 'Testing workflow'}}
        create_response = self.client.post(self.base_url, create_data, format='json')
        assert create_response.status_code == status.HTTP_201_CREATED
        resource_id = create_response.data['id']

        # Read
        read_response = self.client.get(f'{{self.base_url}}{{resource_id}}/')
        assert read_response.status_code == status.HTTP_200_OK
        assert read_response.data['name'] == 'Integration Test'

        # Update
        update_data = {{'name': 'Updated Integration Test'}}
        update_response = self.client.put(f'{{self.base_url}}{{resource_id}}/', update_data, format='json')
        assert update_response.status_code == status.HTTP_200_OK

        # Delete
        delete_response = self.client.delete(f'{{self.base_url}}{{resource_id}}/')
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deleted
        verify_response = self.client.get(f'{{self.base_url}}{{resource_id}}/')
        assert verify_response.status_code == status.HTTP_404_NOT_FOUND

    def test_bulk_operations(self):
        '''Test bulk create and delete operations'''
        # Create multiple
        bulk_data = [
            {{'name': 'Bulk 1', 'description': 'First bulk item'}},
            {{'name': 'Bulk 2', 'description': 'Second bulk item'}},
            {{'name': 'Bulk 3', 'description': 'Third bulk item'}},
        ]

        for data in bulk_data:
            response = self.client.post(self.base_url, data, format='json')
            assert response.status_code == status.HTTP_201_CREATED

        # List all
        list_response = self.client.get(self.base_url)
        assert list_response.status_code == status.HTTP_200_OK
        assert len(list_response.data) >= 3

    def test_filtering_and_pagination_workflow(self):
        '''Test filtering combined with pagination'''
        # Create test data
        for i in range(15):
            {self.resource_name.capitalize()}.objects.create(
                name=f'Test {{i}}',
                description=f'Description {{i}}'
            )

        # Test with filters and pagination
        response = self.client.get(self.base_url + '?limit=5&offset=0')
        assert response.status_code == status.HTTP_200_OK

        # Test with search
        response = self.client.get(self.base_url + '?search=Test&limit=10')
        assert response.status_code == status.HTTP_200_OK

    def test_error_handling_workflow(self):
        '''Test error handling in API workflows'''
        # Test missing required field
        invalid_data = {{}}"
        response = self.client.post(self.base_url, invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        # Test invalid method
        response = self.client.patch(self.base_url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

        # Test not found
        response = self.client.get(f'{{self.base_url}}99999/')
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_concurrent_operations(self):
        '''Test handling of concurrent operations'''
        # Create initial resource
        create_response = self.client.post(self.base_url, {{'name': 'Concurrent Test'}}, format='json')
        resource_id = create_response.data['id']

        # Simulate concurrent updates
        update_data_1 = {{'description': 'Update 1'}}
        update_data_2 = {{'description': 'Update 2'}}

        response_1 = self.client.patch(f'{{self.base_url}}{{resource_id}}/', update_data_1, format='json')
        response_2 = self.client.patch(f'{{self.base_url}}{{resource_id}}/', update_data_2, format='json')

        assert response_1.status_code == status.HTTP_200_OK
        assert response_2.status_code == status.HTTP_200_OK

    def test_transaction_rollback(self):
        '''Test transaction rollback on error'''
        initial_count = {self.resource_name.capitalize()}.objects.count()

        with pytest.raises(Exception):
            with pytest.mark.django_db(transaction=True):
                # Create resource
                self.client.post(self.base_url, {{'name': 'Will fail'}}, format='json')
                # Simulate error that triggers rollback
                raise Exception('Simulated error')

        # Verify rollback
        final_count = {self.resource_name.capitalize()}.objects.count()
        assert initial_count == final_count
"""

    def generate_fastapi_integration_tests(self) -> str:
        """Generate FastAPI integration tests"""
        return f"""
import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy.orm import Session

client = TestClient(app)
BASE_URL = '/api/v1/{self.resource_plural}'

class Test{self.resource_name.capitalize()}IntegrationScenarios:
    '''Integration tests for {self.resource_name} workflows'''

    def test_full_crud_workflow(self):
        '''Test complete CRUD workflow'''
        # Create
        create_data = {{'name': 'Integration Test', 'description': 'Testing workflow'}}
        create_response = client.post(BASE_URL, json=create_data)
        assert create_response.status_code == 201
        resource_id = create_response.json()['id']

        # Read
        read_response = client.get(f'{{BASE_URL}}/{{resource_id}}')
        assert read_response.status_code == 200
        assert read_response.json()['name'] == 'Integration Test'

        # Update
        update_data = {{'name': 'Updated Integration Test'}}
        update_response = client.put(f'{{BASE_URL}}/{{resource_id}}', json=update_data)
        assert update_response.status_code == 200

        # Delete
        delete_response = client.delete(f'{{BASE_URL}}/{{resource_id}}')
        assert delete_response.status_code == 204

        # Verify deleted
        verify_response = client.get(f'{{BASE_URL}}/{{resource_id}}')
        assert verify_response.status_code == 404

    def test_bulk_operations(self):
        '''Test bulk operations'''
        bulk_data = [
            {{'name': 'Bulk 1'}},
            {{'name': 'Bulk 2'}},
            {{'name': 'Bulk 3'}},
        ]

        for data in bulk_data:
            response = client.post(BASE_URL, json=data)
            assert response.status_code == 201

    def test_filtering_workflow(self):
        '''Test filtering with pagination'''
        response = client.get(BASE_URL + '?limit=10&offset=0')
        assert response.status_code == 200

        response = client.get(BASE_URL + '?search=test')
        assert response.status_code == 200

    def test_error_handling(self):
        '''Test error handling'''
        # Invalid data
        response = client.post(BASE_URL, json={{}})
        assert response.status_code == 422

        # Not found
        response = client.get(f'{{BASE_URL}}/99999')
        assert response.status_code == 404

    def test_response_formats(self):
        '''Test different response formats'''
        response = client.get(BASE_URL)
        assert response.status_code == 200
        assert 'application/json' in response.headers.get('content-type', '')

    def test_authentication_workflow(self):
        '''Test authentication in workflows'''
        # Without auth token
        response = client.post(BASE_URL, json={{'name': 'Test'}})
        assert response.status_code in [401, 422]

    def test_pagination_consistency(self):
        '''Test pagination consistency across requests'''
        response1 = client.get(BASE_URL + '?limit=5')
        response2 = client.get(BASE_URL + '?limit=5&offset=5')

        assert response1.status_code == 200
        assert response2.status_code == 200
"""


def generate_integration_tests(
    framework: str,
    resource_name: str,
    resource_plural: str
) -> Dict[str, str]:
    """
    Generate integration tests.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        resource_plural: e.g., "users"

    Returns: dict of {filename: test_code}
    """
    generator = IntegrationTestGenerator(framework, resource_name, resource_plural)
    output = {}

    if framework == "django":
        output[f"test_{resource_name}_integration.py"] = generator.generate_django_integration_tests()
    elif framework == "fastapi":
        output[f"test_{resource_name}_integration.py"] = generator.generate_fastapi_integration_tests()

    return output
