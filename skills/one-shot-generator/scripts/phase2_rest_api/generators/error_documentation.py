"""
Error Documentation Generator - Generate API error documentation

Documents:
- Error codes and meanings
- HTTP status codes
- Error response structure
- Troubleshooting guides
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ErrorCode:
    """Error code documentation"""
    code: str
    http_status: int
    description: str
    example: Optional[str] = None
    possible_causes: Optional[List[str]] = None
    solutions: Optional[List[str]] = None


class ErrorDocumentationGenerator:
    """Generate error documentation"""

    DEFAULT_ERRORS = [
        ErrorCode(
            code="VALIDATION_ERROR",
            http_status=400,
            description="Request validation failed",
            example='{"error": {"code": "VALIDATION_ERROR", "message": "Invalid email format"}}',
            possible_causes=["Invalid input format", "Missing required field", "Invalid data type"],
            solutions=["Check field formats", "Ensure all required fields are present", "Validate data types"]
        ),
        ErrorCode(
            code="AUTHENTICATION_FAILED",
            http_status=401,
            description="Authentication failed or token expired",
            example='{"error": {"code": "AUTHENTICATION_FAILED", "message": "Invalid token"}}',
            possible_causes=["Missing auth token", "Token expired", "Invalid credentials"],
            solutions=["Include Authorization header", "Refresh token", "Check credentials"]
        ),
        ErrorCode(
            code="PERMISSION_DENIED",
            http_status=403,
            description="User lacks required permissions",
            example='{"error": {"code": "PERMISSION_DENIED", "message": "Admin access required"}}',
            possible_causes=["User role too low", "Resource belongs to another user"],
            solutions=["Request higher role", "Verify resource ownership"]
        ),
        ErrorCode(
            code="NOT_FOUND",
            http_status=404,
            description="Resource not found",
            example='{"error": {"code": "NOT_FOUND", "message": "User with id 123 not found"}}',
            possible_causes=["Invalid resource ID", "Resource deleted", "Typo in path"],
            solutions=["Check resource ID", "Verify resource exists"]
        ),
        ErrorCode(
            code="CONFLICT",
            http_status=409,
            description="Resource conflict (e.g., duplicate key)",
            example='{"error": {"code": "CONFLICT", "message": "Email already exists"}}',
            possible_causes=["Duplicate unique field", "Resource already exists"],
            solutions=["Use different value", "Check existing resources"]
        ),
        ErrorCode(
            code="RATE_LIMIT_EXCEEDED",
            http_status=429,
            description="Too many requests",
            example='{"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "Rate limit exceeded"}}',
            possible_causes=["Too many requests in short time"],
            solutions=["Wait before retrying", "Implement exponential backoff"]
        ),
        ErrorCode(
            code="SERVER_ERROR",
            http_status=500,
            description="Internal server error",
            example='{"error": {"code": "SERVER_ERROR", "message": "Internal server error"}}',
            possible_causes=["Server bug", "Database issue", "Unexpected error"],
            solutions=["Contact support", "Check server logs", "Retry request"]
        ),
    ]

    def __init__(self, api_name: str = "API", custom_errors: Optional[List[ErrorCode]] = None):
        self.api_name = api_name
        self.errors = custom_errors or self.DEFAULT_ERRORS

    def generate_markdown(self) -> str:
        """Generate Markdown documentation"""
        doc = f"# {self.api_name} Error Reference\n\n"
        doc += "## Overview\n\n"
        doc += "This document describes all error codes and HTTP status codes that may be returned by the API.\n\n"
        doc += "## Error Response Format\n\n"
        doc += "```json\n"
        doc += '{\n'
        doc += '  "error": {\n'
        doc += '    "code": "ERROR_CODE",\n'
        doc += '    "message": "Human-readable error message",\n'
        doc += '    "status": 400,\n'
        doc += '    "details": {}\n'
        doc += '  }\n'
        doc += '}\n'
        doc += "```\n\n"

        doc += "## Error Codes\n\n"

        for error in self.errors:
            doc += f"### {error.code} ({error.http_status})\n\n"
            doc += f"**Description:** {error.description}\n\n"

            if error.possible_causes:
                doc += "**Possible Causes:**\n"
                for cause in error.possible_causes:
                    doc += f"- {cause}\n"
                doc += "\n"

            if error.solutions:
                doc += "**Solutions:**\n"
                for solution in error.solutions:
                    doc += f"- {solution}\n"
                doc += "\n"

            if error.example:
                doc += "**Example:**\n"
                doc += f"```json\n{error.example}\n```\n\n"

        doc += "## HTTP Status Codes\n\n"
        doc += "| Code | Meaning | Description |\n"
        doc += "|------|---------|-------------|\n"

        status_codes = {}
        for error in self.errors:
            if error.http_status not in status_codes:
                status_codes[error.http_status] = []
            status_codes[error.http_status].append(error.code)

        for status, codes in sorted(status_codes.items()):
            doc += f"| {status} | {self._get_status_text(status)} | {', '.join(codes)} |\n"

        return doc

    def generate_openapi_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI error schema"""
        schemas = {}

        for error in self.errors:
            schemas[error.code] = {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string", "example": error.code},
                            "message": {"type": "string", "example": error.description},
                            "status": {"type": "integer", "example": error.http_status},
                            "details": {"type": "object"}
                        },
                        "required": ["code", "message", "status"]
                    }
                }
            }

        return schemas

    @staticmethod
    def _get_status_text(status_code: int) -> str:
        status_map = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            409: "Conflict",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error"
        }
        return status_map.get(status_code, "Unknown")

    def generate_html(self) -> str:
        """Generate HTML documentation"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{self.api_name} Error Reference</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; padding: 20px; border-radius: 5px; }}
        h1 {{ color: #333; }}
        h2 {{ color: #666; margin-top: 30px; }}
        .error-code {{ background: #f9f9f9; border-left: 4px solid #dc3545; padding: 15px; margin: 10px 0; }}
        .status {{ font-weight: bold; color: #dc3545; }}
        .causes {{ margin: 10px 0; }}
        .solutions {{ margin: 10px 0; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        code {{ background: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
        pre {{ background: #f4f4f4; padding: 10px; border-radius: 3px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{self.api_name} Error Reference</h1>
        <p>This document describes all error codes and HTTP status codes that may be returned by the API.</p>

        <h2>Error Response Format</h2>
        <pre>{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "status": 400,
    "details": {{}}
  }}
}}</pre>

        <h2>Error Codes</h2>
"""

        for error in self.errors:
            html += f"""
        <div class="error-code">
            <h3><span class="status">{error.code}</span> ({error.http_status})</h3>
            <p><strong>Description:</strong> {error.description}</p>
"""
            if error.possible_causes:
                html += '<div class="causes"><strong>Possible Causes:</strong><ul>'
                for cause in error.possible_causes:
                    html += f'<li>{cause}</li>'
                html += '</ul></div>'

            if error.solutions:
                html += '<div class="solutions"><strong>Solutions:</strong><ul>'
                for solution in error.solutions:
                    html += f'<li>{solution}</li>'
                html += '</ul></div>'

            if error.example:
                html += f'<pre>{error.example}</pre>'
            html += '</div>'

        html += """
        <h2>HTTP Status Codes</h2>
        <table>
            <tr>
                <th>Code</th>
                <th>Meaning</th>
                <th>Description</th>
            </tr>
"""

        status_codes = {}
        for error in self.errors:
            if error.http_status not in status_codes:
                status_codes[error.http_status] = []
            status_codes[error.http_status].append(error.code)

        for status, codes in sorted(status_codes.items()):
            html += f"""
            <tr>
                <td>{status}</td>
                <td>{self._get_status_text(status)}</td>
                <td>{', '.join(codes)}</td>
            </tr>
"""

        html += """
        </table>
    </div>
</body>
</html>
"""
        return html


def generate_error_documentation(api_name: str = "API") -> Dict[str, str]:
    """
    Generate error documentation.

    Args:
        api_name: Name of the API

    Returns: dict of {filename: content}
    """
    generator = ErrorDocumentationGenerator(api_name)

    return {
        "errors.md": generator.generate_markdown(),
        "errors.html": generator.generate_html()
    }
