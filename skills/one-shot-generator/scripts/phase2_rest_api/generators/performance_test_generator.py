"""
Performance Test Generator - Load and performance tests

Generates:
- Load testing scenarios
- Performance benchmarks
- Memory profiling tests
- Database query analysis
"""

from typing import Dict, Any, List, Optional


class PerformanceTestGenerator:
    """Generate performance tests"""

    def __init__(self, framework: str, resource_name: str, resource_plural: str):
        self.framework = framework
        self.resource_name = resource_name
        self.resource_plural = resource_plural

    def generate_locust_tests(self) -> str:
        """Generate Locust load testing"""
        return f"""
from locust import HttpUser, task, between
import random

class {self.resource_name.capitalize()}LoadTest(HttpUser):
    '''Load testing for {self.resource_plural} endpoints'''

    wait_time = between(1, 3)

    def on_start(self):
        '''Initialize test user'''
        self.ids = []

    @task(2)
    def list_{self.resource_plural}(self):
        '''Load test list endpoint'''
        self.client.get(
            '/api/v1/{self.resource_plural}/',
            headers={{'Authorization': 'Bearer test-token'}}
        )

    @task(1)
    def create_{self.resource_name}(self):
        '''Load test create endpoint'''
        data = {{'name': f'Load test {{random.randint(0, 10000)}}'}}
        response = self.client.post(
            '/api/v1/{self.resource_plural}/',
            json=data,
            headers={{'Authorization': 'Bearer test-token'}}
        )
        if response.status_code == 201:
            self.ids.append(response.json()['id'])

    @task(1)
    def retrieve_{self.resource_name}(self):
        '''Load test retrieve endpoint'''
        if self.ids:
            resource_id = random.choice(self.ids)
            self.client.get(
                f'/api/v1/{self.resource_plural}/{{resource_id}}/',
                headers={{'Authorization': 'Bearer test-token'}}
            )

    @task(1)
    def update_{self.resource_name}(self):
        '''Load test update endpoint'''
        if self.ids:
            resource_id = random.choice(self.ids)
            data = {{'name': 'Updated'}}
            self.client.put(
                f'/api/v1/{self.resource_plural}/{{resource_id}}/',
                json=data,
                headers={{'Authorization': 'Bearer test-token'}}
            )

    @task(1)
    def delete_{self.resource_name}(self):
        '''Load test delete endpoint'''
        if self.ids:
            resource_id = self.ids.pop()
            self.client.delete(
                f'/api/v1/{self.resource_plural}/{{resource_id}}/',
                headers={{'Authorization': 'Bearer test-token'}}
            )
"""

    def generate_pytest_performance_tests(self) -> str:
        """Generate pytest performance tests"""
        return f"""
import pytest
import time
from django.test import TestCase, TransactionTestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.mark.django_db
class Test{self.resource_name.capitalize()}Performance(TestCase):
    '''Performance tests for {self.resource_name} API'''

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('perftest', 'perf@test.com', 'pass')
        self.client.force_authenticate(self.user)

    def test_list_performance(self):
        '''Test list endpoint performance'''
        from ..models import {self.resource_name.capitalize()}

        # Create 100 objects
        for i in range(100):
            {self.resource_name.capitalize()}.objects.create(name=f'Perf Test {{i}}')

        # Time the list endpoint
        start = time.time()
        response = self.client.get('/api/v1/{self.resource_plural}/?limit=50')
        duration = time.time() - start

        assert response.status_code == 200
        assert duration < 1.0, f'List endpoint took {{duration}}s, expected < 1s'

    def test_create_performance(self):
        '''Test create endpoint performance'''
        start = time.time()
        response = self.client.post(
            '/api/v1/{self.resource_plural}/',
            {{'name': 'Performance Test'}},
            format='json'
        )
        duration = time.time() - start

        assert response.status_code == 201
        assert duration < 0.5, f'Create endpoint took {{duration}}s, expected < 0.5s'

    def test_bulk_create_performance(self):
        '''Test bulk create performance'''
        start = time.time()

        for i in range(50):
            self.client.post(
                '/api/v1/{self.resource_plural}/',
                {{'name': f'Bulk {{i}}'}},
                format='json'
            )

        duration = time.time() - start
        avg_time = duration / 50

        assert avg_time < 0.1, f'Avg create time {{avg_time}}s, expected < 0.1s'

    def test_query_performance(self, django_db_blocker):
        '''Test database query performance'''
        from django.test.utils import override_settings
        from django.core.management import call_command
        from ..models import {self.resource_name.capitalize()}

        django_db_blocker.unblock()

        # Create test data
        with override_settings(DEBUG=True):
            from django.db import connection
            from django.test.utils import CaptureQueriesContext

            # Create 10 objects
            for i in range(10):
                {self.resource_name.capitalize()}.objects.create(name=f'Query {{i}}')

            # Measure queries
            with CaptureQueriesContext(connection) as ctx:
                response = self.client.get('/api/v1/{self.resource_plural}/')

            # Should not have N+1 queries
            assert len(ctx.captured_queries) < 15, f'Too many queries: {{len(ctx.captured_queries)}}'
"""

    def generate_memory_profiling_tests(self) -> str:
        """Generate memory profiling tests"""
        return f"""
import pytest
import tracemalloc
from memory_profiler import profile

class Test{self.resource_name.capitalize()}MemoryUsage:
    '''Memory profiling tests'''

    @profile
    def test_list_memory_usage(self):
        '''Test memory usage of list endpoint'''
        tracemalloc.start()

        # Simulate listing many items
        items = [
            {{'id': i, 'name': 'Item {{i}}'}}
            for i in range(1000)
        ]

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Memory should not exceed 10MB
        assert peak < 10 * 1024 * 1024, f'Peak memory {{peak}} exceeds limit'

    @profile
    def test_create_memory_usage(self):
        '''Test memory usage of create endpoint'''
        tracemalloc.start()

        # Simulate creating many items
        for i in range(100):
            data = {{'name': f'Item {{i}}', 'description': 'Test' * 100}}

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        assert peak < 5 * 1024 * 1024, f'Peak memory {{peak}} exceeds limit'
"""

    def generate_benchmark_script(self) -> str:
        """Generate benchmark script"""
        return f"""
import time
import requests
from typing import Dict, List

class APIBenchmark:
    '''Benchmark API performance'''

    def __init__(self, base_url: str = 'http://localhost:8000'):
        self.base_url = base_url
        self.results = {{}}

    def benchmark_list_endpoint(self, iterations: int = 100):
        '''Benchmark list endpoint'''
        times = []

        for _ in range(iterations):
            start = time.time()
            response = requests.get(f'{{self.base_url}}/api/v1/{self.resource_plural}/')
            duration = time.time() - start
            times.append(duration)

        self.results['list'] = {{
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'iterations': iterations
        }}

    def benchmark_create_endpoint(self, iterations: int = 50):
        '''Benchmark create endpoint'''
        times = []

        for i in range(iterations):
            data = {{'name': f'Benchmark {{i}}'}}
            start = time.time()
            response = requests.post(
                f'{{self.base_url}}/api/v1/{self.resource_plural}/',
                json=data
            )
            duration = time.time() - start
            times.append(duration)

        self.results['create'] = {{
            'min': min(times),
            'max': max(times),
            'avg': sum(times) / len(times),
            'iterations': iterations
        }}

    def print_results(self):
        '''Print benchmark results'''
        print('\\nBenchmark Results:')
        print('-' * 50)
        for endpoint, metrics in self.results.items():
            print(f'\\n{{endpoint.upper()}} ENDPOINT:')
            print(f'  Min:        {{metrics["min"]:.4f}}s')
            print(f'  Max:        {{metrics["max"]:.4f}}s')
            print(f'  Avg:        {{metrics["avg"]:.4f}}s')
            print(f'  Iterations: {{metrics["iterations"]}}')

if __name__ == '__main__':
    benchmark = APIBenchmark()
    benchmark.benchmark_list_endpoint(100)
    benchmark.benchmark_create_endpoint(50)
    benchmark.print_results()
"""


def generate_performance_tests(
    framework: str,
    resource_name: str,
    resource_plural: str
) -> Dict[str, str]:
    """
    Generate performance tests.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"
        resource_plural: e.g., "users"

    Returns: dict of {filename: test_code}
    """
    generator = PerformanceTestGenerator(framework, resource_name, resource_plural)
    output = {}

    output[f"test_{resource_name}_performance.py"] = generator.generate_pytest_performance_tests()
    output["test_load_locust.py"] = generator.generate_locust_tests()
    output["test_memory.py"] = generator.generate_memory_profiling_tests()
    output["benchmark.py"] = generator.generate_benchmark_script()

    return output
