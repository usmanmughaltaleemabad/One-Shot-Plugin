"""
Mock Generator - Mocks and stubs for testing

Generates:
- Mock objects for external services
- Stub responses
- Mock database
- Mock authentication
"""

from typing import Dict, Any, List, Optional


class MockGenerator:
    """Generate mock objects"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_service_mocks(self) -> str:
        """Generate service mocks"""
        return f"""
from unittest.mock import Mock, MagicMock, patch
import pytest

class Mock{self.resource_name.capitalize()}Service:
    '''Mock {self.resource_name} service'''

    def __init__(self):
        self.calls = []

    def create(self, data):
        self.calls.append(('create', data))
        return {{'id': 1, **data}}

    def get(self, id):
        self.calls.append(('get', id))
        return {{'id': id, 'name': '{self.resource_name.capitalize()}'}}

    def list(self, filters=None):
        self.calls.append(('list', filters))
        return [
            {{'id': 1, 'name': '{self.resource_name.capitalize()} 1'}},
            {{'id': 2, 'name': '{self.resource_name.capitalize()} 2'}},
        ]

    def update(self, id, data):
        self.calls.append(('update', id, data))
        return {{'id': id, **data}}

    def delete(self, id):
        self.calls.append(('delete', id))
        return {{'deleted': True}}

    def assert_called_with(self, method, *args):
        '''Assert that method was called with specific arguments'''
        for call in self.calls:
            if call[0] == method and call[1:] == args:
                return True
        return False

    def reset(self):
        '''Reset call history'''
        self.calls = []

@pytest.fixture
def mock_{self.resource_name}_service():
    return Mock{self.resource_name.capitalize()}Service()
"""

    def generate_external_service_mocks(self) -> str:
        """Generate mocks for external services"""
        return """
from unittest.mock import Mock, patch
import pytest

class MockEmailService:
    '''Mock email service'''
    def send(self, to, subject, body):
        return {'sent': True, 'to': to}

class MockNotificationService:
    '''Mock notification service'''
    def notify(self, user_id, message):
        return {'notified': True, 'user_id': user_id}

class MockPaymentService:
    '''Mock payment service'''
    def charge(self, user_id, amount):
        return {'success': True, 'amount': amount, 'user_id': user_id}

    def refund(self, transaction_id):
        return {'refunded': True, 'transaction_id': transaction_id}

class MockStorageService:
    '''Mock file storage service'''
    def upload(self, file_path, content):
        return {'url': f'https://example.com/{file_path}'}

    def download(self, file_path):
        return {'content': b'file content'}

    def delete(self, file_path):
        return {'deleted': True}

@pytest.fixture
def mock_email_service():
    return MockEmailService()

@pytest.fixture
def mock_notification_service():
    return MockNotificationService()

@pytest.fixture
def mock_payment_service():
    return MockPaymentService()

@pytest.fixture
def mock_storage_service():
    return MockStorageService()
"""

    def generate_mock_database(self) -> str:
        """Generate mock database"""
        return f"""
from typing import Dict, List
import pytest

class MockDatabase:
    '''Mock in-memory database for testing'''

    def __init__(self):
        self.data: Dict[str, List[Dict]] = {{
            '{self.resource_name}s': []
        }}
        self.next_id = 1

    def create(self, table: str, data: Dict) -> Dict:
        '''Create a record'''
        record = {{'id': self.next_id, **data}}
        self.next_id += 1
        self.data[table].append(record)
        return record

    def read(self, table: str, id: int) -> Dict:
        '''Read a record'''
        for record in self.data[table]:
            if record['id'] == id:
                return record
        return None

    def update(self, table: str, id: int, data: Dict) -> Dict:
        '''Update a record'''
        for record in self.data[table]:
            if record['id'] == id:
                record.update(data)
                return record
        return None

    def delete(self, table: str, id: int) -> bool:
        '''Delete a record'''
        self.data[table] = [r for r in self.data[table] if r['id'] != id]
        return True

    def list(self, table: str) -> List[Dict]:
        '''List all records'''
        return self.data[table]

    def clear(self, table: str):
        '''Clear all records in table'''
        self.data[table] = []

    def reset(self):
        '''Reset all data'''
        self.__init__()

@pytest.fixture
def mock_db():
    db = MockDatabase()
    yield db
    db.reset()
"""

    def generate_mock_auth(self) -> str:
        """Generate mock authentication"""
        return """
from unittest.mock import Mock, patch
import pytest
from datetime import datetime, timedelta
import jwt

class MockAuthService:
    '''Mock authentication service'''

    def __init__(self, secret='test-secret'):
        self.secret = secret

    def generate_token(self, user_id: int, expires_in: int = 3600):
        '''Generate JWT token'''
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret, algorithm='HS256')

    def verify_token(self, token: str):
        '''Verify JWT token'''
        try:
            return jwt.decode(token, self.secret, algorithms=['HS256'])
        except:
            return None

    def create_user(self, username: str, password: str):
        '''Create a mock user'''
        return {
            'id': 1,
            'username': username,
            'password': password,  # In real code, hash this!
            'created_at': datetime.utcnow().isoformat()
        }

    def authenticate(self, username: str, password: str):
        '''Authenticate user'''
        return {
            'token': self.generate_token(1),
            'user': {'id': 1, 'username': username}
        }

@pytest.fixture
def mock_auth_service():
    return MockAuthService()
"""


def generate_mocks(framework: str, resource_name: str) -> Dict[str, str]:
    """
    Generate mock objects.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"

    Returns: dict of {filename: mock_code}
    """
    generator = MockGenerator(framework, resource_name)
    output = {}

    output["mock_services.py"] = generator.generate_service_mocks()
    output["mock_external_services.py"] = generator.generate_external_service_mocks()
    output["mock_database.py"] = generator.generate_mock_database()
    output["mock_auth.py"] = generator.generate_mock_auth()

    return output
