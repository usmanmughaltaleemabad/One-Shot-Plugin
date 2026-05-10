"""
OpenAPI/Swagger Generator - Auto-generate API documentation

Generates:
- OpenAPI 3.0 specification
- Swagger UI configuration
- Request/response examples
- Error documentation
- Authentication schemes
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime


class OpenAPIGenerator:
    """Generate OpenAPI specification"""

    def __init__(self, title: str, version: str, description: str = "", base_path: str = "/api/v1"):
        self.title = title
        self.version = version
        self.description = description
        self.base_path = base_path
        self.paths: Dict[str, Dict] = {}
        self.schemas: Dict[str, Dict] = {}

    def add_resource(
        self,
        resource_name: str,
        resource_plural: str,
        schema: Dict[str, Any],
        operations: List[str] = None
    ):
        """
        Add a resource with CRUD operations to OpenAPI spec.

        Args:
            resource_name: e.g., "user"
            resource_plural: e.g., "users"
            schema: JSON schema for the resource
            operations: list of operations (create, read, update, delete, list)
        """
        if operations is None:
            operations = ["list", "create", "retrieve", "update", "delete"]

        path = f"{self.base_path}/{resource_plural}"
        item_path = f"{path}/{{id}}"

        # Add schemas
        self.schemas[self._schema_name(resource_name)] = schema
        self.schemas[f"{self._schema_name(resource_name)}Create"] = self._create_schema(schema)
        self.schemas[f"{self._schema_name(resource_name)}Update"] = self._update_schema(schema)

        # Add paths
        if "list" in operations:
            self._add_list_operation(path, resource_name, resource_plural)
        if "create" in operations:
            self._add_create_operation(path, resource_name)
        if "retrieve" in operations:
            self._add_retrieve_operation(item_path, resource_name)
        if "update" in operations:
            self._add_update_operation(item_path, resource_name)
        if "delete" in operations:
            self._add_delete_operation(item_path, resource_name)

    def _add_list_operation(self, path: str, resource_name: str, resource_plural: str):
        """Add GET list operation"""
        if path not in self.paths:
            self.paths[path] = {}

        self.paths[path]["get"] = {
            "summary": f"List {resource_plural}",
            "description": f"Retrieve a paginated list of all {resource_plural}",
            "tags": [resource_name],
            "parameters": [
                {
                    "name": "skip",
                    "in": "query",
                    "description": "Number of items to skip",
                    "required": False,
                    "schema": {"type": "integer", "default": 0}
                },
                {
                    "name": "limit",
                    "in": "query",
                    "description": "Number of items to return",
                    "required": False,
                    "schema": {"type": "integer", "default": 20, "maximum": 100}
                },
                {
                    "name": "search",
                    "in": "query",
                    "description": "Search query",
                    "required": False,
                    "schema": {"type": "string"}
                }
            ],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "results": {
                                        "type": "array",
                                        "items": {"$ref": f"#/components/schemas/{self._schema_name(resource_name)}"}
                                    },
                                    "total": {"type": "integer"},
                                    "skip": {"type": "integer"},
                                    "limit": {"type": "integer"}
                                }
                            }
                        }
                    }
                },
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "403": {"$ref": "#/components/responses/Forbidden"}
            },
            "security": [{"bearerAuth": []}]
        }

    def _add_create_operation(self, path: str, resource_name: str):
        """Add POST create operation"""
        if path not in self.paths:
            self.paths[path] = {}

        self.paths[path]["post"] = {
            "summary": f"Create {resource_name}",
            "description": f"Create a new {resource_name}",
            "tags": [resource_name],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{self._schema_name(resource_name)}Create"}
                    }
                }
            },
            "responses": {
                "201": {
                    "description": "Resource created successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{self._schema_name(resource_name)}"}
                        }
                    }
                },
                "400": {"$ref": "#/components/responses/BadRequest"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "422": {"$ref": "#/components/responses/ValidationError"}
            },
            "security": [{"bearerAuth": []}]
        }

    def _add_retrieve_operation(self, path: str, resource_name: str):
        """Add GET by ID operation"""
        if path not in self.paths:
            self.paths[path] = {}

        self.paths[path]["get"] = {
            "summary": f"Retrieve {resource_name}",
            "description": f"Get a single {resource_name} by ID",
            "tags": [resource_name],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "description": "Resource ID",
                    "required": True,
                    "schema": {"type": "integer"}
                }
            ],
            "responses": {
                "200": {
                    "description": "Successful response",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{self._schema_name(resource_name)}"}
                        }
                    }
                },
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "404": {"$ref": "#/components/responses/NotFound"}
            },
            "security": [{"bearerAuth": []}]
        }

    def _add_update_operation(self, path: str, resource_name: str):
        """Add PUT/PATCH update operation"""
        if path not in self.paths:
            self.paths[path] = {}

        self.paths[path]["put"] = {
            "summary": f"Update {resource_name}",
            "description": f"Update a {resource_name}",
            "tags": [resource_name],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "description": "Resource ID",
                    "required": True,
                    "schema": {"type": "integer"}
                }
            ],
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": {"$ref": f"#/components/schemas/{self._schema_name(resource_name)}Update"}
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Resource updated successfully",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{self._schema_name(resource_name)}"}
                        }
                    }
                },
                "400": {"$ref": "#/components/responses/BadRequest"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "404": {"$ref": "#/components/responses/NotFound"},
                "422": {"$ref": "#/components/responses/ValidationError"}
            },
            "security": [{"bearerAuth": []}]
        }

    def _add_delete_operation(self, path: str, resource_name: str):
        """Add DELETE operation"""
        if path not in self.paths:
            self.paths[path] = {}

        self.paths[path]["delete"] = {
            "summary": f"Delete {resource_name}",
            "description": f"Delete a {resource_name}",
            "tags": [resource_name],
            "parameters": [
                {
                    "name": "id",
                    "in": "path",
                    "description": "Resource ID",
                    "required": True,
                    "schema": {"type": "integer"}
                }
            ],
            "responses": {
                "204": {"description": "Resource deleted successfully"},
                "401": {"$ref": "#/components/responses/Unauthorized"},
                "404": {"$ref": "#/components/responses/NotFound"}
            },
            "security": [{"bearerAuth": []}]
        }

    def _schema_name(self, resource_name: str) -> str:
        """Convert resource name to schema name"""
        return resource_name.capitalize()

    def _create_schema(self, schema: Dict) -> Dict:
        """Generate create schema (without id, timestamps)"""
        create_schema = schema.copy()
        # Remove read-only fields
        for field in ["id", "created_at", "updated_at"]:
            create_schema.pop(field, None)
        return create_schema

    def _update_schema(self, schema: Dict) -> Dict:
        """Generate update schema (all fields optional)"""
        update_schema = self._create_schema(schema)
        # Make all properties not required
        update_schema["required"] = []
        return update_schema

    def generate(self) -> str:
        """Generate complete OpenAPI spec as JSON string"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.title,
                "version": self.version,
                "description": self.description,
                "contact": {
                    "name": "API Support",
                    "url": "https://example.com/support"
                }
            },
            "servers": [
                {
                    "url": self.base_path,
                    "description": "Production server"
                }
            ],
            "paths": self.paths,
            "components": {
                "schemas": self.schemas,
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                },
                "responses": {
                    "BadRequest": {
                        "description": "Bad request",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {"type": "string"},
                                        "status": {"type": "integer"}
                                    }
                                }
                            }
                        }
                    },
                    "Unauthorized": {
                        "description": "Unauthorized",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"detail": {"type": "string"}}
                                }
                            }
                        }
                    },
                    "Forbidden": {
                        "description": "Forbidden",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"detail": {"type": "string"}}
                                }
                            }
                        }
                    },
                    "NotFound": {
                        "description": "Not found",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {"detail": {"type": "string"}}
                                }
                            }
                        }
                    },
                    "ValidationError": {
                        "description": "Validation error",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "detail": {
                                            "type": "array",
                                            "items": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "security": [{"bearerAuth": []}]
        }

        return json.dumps(spec, indent=2)


def generate_openapi_spec(
    api_title: str,
    api_version: str,
    resources: List[Dict],
    description: str = ""
) -> str:
    """
    Generate OpenAPI specification.

    Args:
        api_title: API title
        api_version: API version
        resources: list of resource dicts with name, plural, schema
        description: API description

    Returns: OpenAPI spec as JSON string
    """
    generator = OpenAPIGenerator(api_title, api_version, description)

    for resource in resources:
        generator.add_resource(
            resource_name=resource.get("name"),
            resource_plural=resource.get("plural", f"{resource.get('name')}s"),
            schema=resource.get("schema", {}),
            operations=resource.get("operations")
        )

    return generator.generate()
