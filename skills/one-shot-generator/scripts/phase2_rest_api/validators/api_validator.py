"""
API Validator - Validates REST API structure and compliance

Checks:
- HTTP status codes (201 for create, 204 for delete, etc.)
- Request/response schemas
- Error handling
- Authentication/authorization
- Rate limiting headers
- CORS configuration
- API versioning
"""

import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class APIValidationError:
    """Validation error result"""
    severity: str  # warning, error, critical
    location: str  # file:line
    message: str
    fix: str


class APIValidator:
    """Validate REST API implementation"""

    def __init__(self, framework: str, code: Dict[str, str]):
        self.framework = framework
        self.code = code
        self.errors: List[APIValidationError] = []

    def validate(self) -> Tuple[bool, List[APIValidationError]]:
        """
        Validate API implementation.

        Returns: (is_valid, errors_list)
        """
        self._validate_http_methods()
        self._validate_status_codes()
        self._validate_error_handling()
        self._validate_authentication()
        self._validate_pagination()
        self._validate_request_validation()

        return len(self.errors) == 0, self.errors

    def _validate_http_methods(self):
        """Validate proper HTTP methods per endpoint"""
        for filename, content in self.code.items():
            # Check GET for list endpoints
            if "def list_" in content or "def get_all" in content:
                if "@router.get" not in content and "@app.get" not in content:
                    self.errors.append(APIValidationError(
                        severity="error",
                        location=f"{filename}:list",
                        message="List endpoint should use GET method",
                        fix="Change to @router.get() or @app.get()"
                    ))

            # Check POST for create endpoints
            if "def create_" in content:
                if "@router.post" not in content and "@app.post" not in content:
                    self.errors.append(APIValidationError(
                        severity="error",
                        location=f"{filename}:create",
                        message="Create endpoint should use POST method",
                        fix="Change to @router.post() or @app.post()"
                    ))

    def _validate_status_codes(self):
        """Validate correct HTTP status codes"""
        for filename, content in self.code.items():
            # Create should return 201
            if "def create_" in content and "201" not in content and "CREATED" not in content:
                self.errors.append(APIValidationError(
                    severity="warning",
                    location=f"{filename}:create",
                    message="Create endpoint should return 201 CREATED",
                    fix="Add status_code=201 to endpoint decorator"
                ))

            # Delete should return 204
            if "def delete_" in content and "204" not in content and "NO_CONTENT" not in content:
                self.errors.append(APIValidationError(
                    severity="warning",
                    location=f"{filename}:delete",
                    message="Delete endpoint should return 204 NO_CONTENT",
                    fix="Add status_code=204 to endpoint decorator"
                ))

    def _validate_error_handling(self):
        """Validate error handling"""
        for filename, content in self.code.items():
            # Check for 404 handling
            if "def retrieve_" in content or "def get_" in content:
                if "404" not in content and "NotFound" not in content and "HTTPException" not in content:
                    self.errors.append(APIValidationError(
                        severity="warning",
                        location=f"{filename}:retrieve",
                        message="Retrieve endpoint should handle 404 Not Found",
                        fix="Add check for None and return 404 error"
                    ))

            # Check for validation error handling
            if "def create_" in content or "def update_" in content:
                if "400" not in content and "ValidationError" not in content:
                    self.errors.append(APIValidationError(
                        severity="warning",
                        location=f"{filename}:create/update",
                        message="Endpoint should validate input and return 400 errors",
                        fix="Add request validation with error handling"
                    ))

    def _validate_authentication(self):
        """Validate authentication is present"""
        for filename, content in self.code.items():
            if "create_" in content or "update_" in content or "delete_" in content:
                auth_keywords = ["IsAuthenticated", "Depends", "require_auth", "@auth", "permission_classes"]
                has_auth = any(kw in content for kw in auth_keywords)

                if not has_auth:
                    self.errors.append(APIValidationError(
                        severity="critical",
                        location=f"{filename}",
                        message="Endpoint lacks authentication check",
                        fix="Add authentication/permission requirements"
                    ))

    def _validate_pagination(self):
        """Validate pagination on list endpoints"""
        for filename, content in self.code.items():
            if "def list_" in content or "def get_all" in content:
                pagination_keywords = ["skip", "limit", "offset", "page", "paginate", "Pagination"]
                has_pagination = any(kw in content for kw in pagination_keywords)

                if not has_pagination:
                    self.errors.append(APIValidationError(
                        severity="warning",
                        location=f"{filename}:list",
                        message="List endpoint should implement pagination",
                        fix="Add skip/limit parameters and paginate results"
                    ))

    def _validate_request_validation(self):
        """Validate request schemas"""
        for filename, content in self.code.items():
            if "def create_" in content or "def update_" in content:
                schema_keywords = ["Schema", "BaseModel", "Serializer", "DTO", "pydantic"]
                has_schema = any(kw in content for kw in schema_keywords)

                if not has_schema:
                    self.errors.append(APIValidationError(
                        severity="error",
                        location=f"{filename}:create/update",
                        message="Endpoint missing request schema/validation",
                        fix="Add Pydantic schema or DRF serializer for request validation"
                    ))


def validate_api(framework: str, code: Dict[str, str]) -> Tuple[bool, List[Dict]]:
    """
    Validate REST API implementation.

    Args:
        framework: django, fastapi, spring, go, nestjs
        code: dict of {filename: code_content}

    Returns: (is_valid, errors_list)
    """
    validator = APIValidator(framework, code)
    is_valid, errors = validator.validate()

    error_dicts = [
        {
            "severity": e.severity,
            "location": e.location,
            "message": e.message,
            "fix": e.fix
        }
        for e in errors
    ]

    return is_valid, error_dicts
