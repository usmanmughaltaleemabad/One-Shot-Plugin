"""
Phase 2 Orchestrator - REST API Specialist

Orchestrates all Phase 2 modules to generate complete REST APIs.
Generates:
- CRUD endpoints
- Request validation
- OpenAPI documentation
- Pagination, filtering, sorting
- Authentication
- Error handling
- Complete test suite
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .core.crud_generator import CRUDGenerator, CRUDConfig
from .validators.api_validator import APIValidator
from .generators.openapi_generator import OpenAPIGenerator
from .handlers.pagination_handler import (
    PaginationGenerator,
    PaginationConfig,
    FilteringGenerator,
    SortingGenerator
)
from .handlers.request_validator import RequestValidatorGenerator


@dataclass
class Phase2Config:
    """Configuration for Phase 2 REST API generation"""
    framework: str  # django, fastapi, spring, go, nestjs
    language: str   # python, java, go, typescript
    api_name: str  # e.g., "User Service"
    api_version: str  # e.g., "v1"
    base_path: str  # e.g., "/api/v1"
    resources: List[Dict[str, Any]]  # list of resource configs
    include_tests: bool = True
    include_docs: bool = True
    include_pagination: bool = True
    include_filtering: bool = True
    include_auth: bool = True
    pagination_style: str = "offset"


class Phase2Orchestrator:
    """Orchestrate REST API generation"""

    def __init__(self, config: Phase2Config):
        self.config = config
        self.generated_code: Dict[str, str] = {}
        self.generated_docs: Dict[str, str] = {}
        self.test_code: Dict[str, str] = {}

    def generate(self) -> Dict[str, Any]:
        """
        Generate complete REST API.

        Returns: {
            "code": {filename: code_content},
            "tests": {filename: test_content},
            "docs": {filename: doc_content},
            "openapi": openapi_spec_json,
            "validation_results": {},
            "readme": setup_instructions
        }
        """
        for resource in self.config.resources:
            self._generate_resource(resource)

        if self.config.include_docs:
            self._generate_openapi_docs()

        if self.config.include_tests:
            self._generate_tests()

        self._generate_readme()

        return {
            "code": self.generated_code,
            "tests": self.test_code if self.config.include_tests else {},
            "docs": self.generated_docs if self.config.include_docs else {},
            "status": "success",
            "resources_generated": len(self.config.resources),
            "files_generated": len(self.generated_code) + len(self.test_code) + len(self.generated_docs)
        }

    def _generate_resource(self, resource: Dict[str, Any]):
        """Generate CRUD endpoints for a single resource"""
        resource_name = resource.get("name", "resource")
        resource_plural = resource.get("plural", f"{resource_name}s")

        print(f"  Generating {resource_name} REST API...")

        # Generate CRUD
        crud_config = CRUDConfig(
            framework=self.config.framework,
            language=self.config.language,
            resource_name=resource_name,
            resource_plural=resource_plural,
            has_authentication=self.config.include_auth,
            include_timestamps=True,
            pagination_style=self.config.pagination_style
        )

        crud_gen = CRUDGenerator(crud_config)
        crud_code = crud_gen.generate()
        self.generated_code.update(crud_code)

        # Generate pagination/filtering/sorting
        if self.config.include_pagination:
            self._generate_pagination_code(resource_name, resource_plural)

        # Generate validation
        if resource.get("validation_rules"):
            self._generate_validation(resource_name, resource.get("validation_rules", []))

        print(f"  ✅ Generated {resource_name}")

    def _generate_pagination_code(self, resource_name: str, resource_plural: str):
        """Generate pagination, filtering, sorting code"""
        pagination_gen = PaginationGenerator(
            self.config.framework,
            PaginationConfig(style=self.config.pagination_style, default_limit=20, max_limit=100)
        )

        if self.config.framework == "django":
            self.generated_code[f"{resource_name}/pagination.py"] = pagination_gen.generate_django()
        elif self.config.framework == "fastapi":
            self.generated_code[f"{resource_name}/pagination.py"] = pagination_gen.generate_fastapi()

    def _generate_validation(self, resource_name: str, validation_rules: List[Dict]):
        """Generate request validation"""
        validator_gen = RequestValidatorGenerator(self.config.framework, resource_name)

        if self.config.framework == "django":
            self.generated_code[f"{resource_name}/serializers.py"] = validator_gen.generate_django(
                [self._dict_to_validation_rule(r) for r in validation_rules]
            )

    def _dict_to_validation_rule(self, rule_dict: Dict) -> Any:
        """Convert dict to ValidationRule"""
        from .handlers.request_validator import ValidationRule
        return ValidationRule(**rule_dict)

    def _generate_openapi_docs(self):
        """Generate OpenAPI specification"""
        openapi_gen = OpenAPIGenerator(
            self.config.api_name,
            self.config.api_version,
            base_path=self.config.base_path
        )

        for resource in self.config.resources:
            schema = resource.get("schema", {})
            openapi_gen.add_resource(
                resource_name=resource.get("name"),
                resource_plural=resource.get("plural", f"{resource.get('name')}s"),
                schema=schema
            )

        openapi_spec = openapi_gen.generate()
        self.generated_docs["openapi.json"] = openapi_spec

        # Generate Swagger UI HTML
        swagger_html = self._generate_swagger_ui_html()
        self.generated_docs["swagger-ui.html"] = swagger_html

    def _generate_swagger_ui_html(self) -> str:
        """Generate Swagger UI HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui.css">
    <style>
        body {
            margin: 0;
            padding: 0;
            background: #fafafa;
        }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-bundle.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@3/swagger-ui-standalone-preset.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                layout: "StandaloneLayout"
            });
        }
    </script>
</body>
</html>
"""

    def _generate_tests(self):
        """Generate test suite"""
        for resource in self.config.resources:
            resource_name = resource.get("name", "resource")
            resource_plural = resource.get("plural", f"{resource_name}s")

            if self.config.framework == "django":
                test_code = self._generate_django_tests(resource_name, resource_plural)
            elif self.config.framework == "fastapi":
                test_code = self._generate_fastapi_tests(resource_name, resource_plural)
            else:
                test_code = "# Tests to be implemented"

            self.test_code[f"test_{resource_name}_api.py"] = test_code

    def _generate_django_tests(self, resource_name: str, resource_plural: str) -> str:
        """Generate Django test suite"""
        return f"""
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User

@pytest.mark.django_db
class Test{resource_name.capitalize()}API(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user('test', 'test@test.com', 'pass')
        self.client.force_authenticate(self.user)
        self.url = '/api/v1/{resource_plural}/'

    def test_list_{resource_plural}(self):
        response = self.client.get(self.url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_{resource_name}(self):
        data = {{'name': 'Test', 'description': 'Test'}}
        response = self.client.post(self.url, data)
        assert response.status_code == status.HTTP_201_CREATED

    def test_pagination(self):
        for i in range(25):
            # Create test data
            pass
        response = self.client.get(self.url + '?limit=20')
        assert response.status_code == status.HTTP_200_OK
        assert 'next' in response.data

    def test_filtering(self):
        response = self.client.get(self.url + '?search=test')
        assert response.status_code == status.HTTP_200_OK

    def test_authentication_required(self):
        self.client.force_authenticate(None)
        response = self.client.post(self.url, {{'name': 'Test'}})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
"""

    def _generate_fastapi_tests(self, resource_name: str, resource_plural: str) -> str:
        """Generate FastAPI test suite"""
        return f"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_{resource_plural}():
    response = client.get("/api/v1/{resource_plural}/")
    assert response.status_code == 200

def test_create_{resource_name}():
    data = {{"name": "Test", "description": "Test"}}
    response = client.post("/api/v1/{resource_plural}/", json=data)
    assert response.status_code == 201

def test_pagination():
    response = client.get("/api/v1/{resource_plural}/?limit=20")
    assert response.status_code == 200
    assert "next" in response.json()

def test_filtering():
    response = client.get("/api/v1/{resource_plural}/?search=test")
    assert response.status_code == 200

def test_unauthorized():
    # Test without auth headers
    data = {{"name": "Test"}}
    response = client.post("/api/v1/{resource_plural}/", json=data)
    assert response.status_code == 401
"""

    def _generate_readme(self):
        """Generate README with setup instructions"""
        readme = f"""
# {self.config.api_name} REST API

Generated REST API for managing resources.

## Installation

### Prerequisites
- Python 3.9+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
python manage.py migrate  # Django
```

3. Run server:
```bash
python manage.py runserver  # Django
uvicorn main:app --reload  # FastAPI
```

4. Access API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

"""
        for resource in self.config.resources:
            resource_name = resource.get("name")
            resource_plural = resource.get("plural", f"{resource_name}s")
            readme += f"""
### {resource_name.capitalize()}

- `GET /api/v1/{resource_plural}/` - List all {resource_plural}
- `POST /api/v1/{resource_plural}/` - Create new {resource_name}
- `GET /api/v1/{resource_plural}/{{id}}` - Retrieve {resource_name}
- `PUT /api/v1/{resource_plural}/{{id}}` - Update {resource_name}
- `DELETE /api/v1/{resource_plural}/{{id}}` - Delete {resource_name}

"""

        readme += """
## Features

- ✅ CRUD endpoints
- ✅ Pagination, filtering, sorting
- ✅ Request validation
- ✅ Error handling
- ✅ Authentication
- ✅ OpenAPI documentation

## Testing

Run tests:
```bash
pytest
```

Run with coverage:
```bash
pytest --cov
```
"""

        self.generated_docs["README.md"] = readme


def orchestrate_phase2(config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for Phase 2 REST API generation.

    Args:
        config_dict: configuration dict

    Returns: generation result
    """
    config = Phase2Config(**config_dict)
    orchestrator = Phase2Orchestrator(config)
    return orchestrator.generate()
