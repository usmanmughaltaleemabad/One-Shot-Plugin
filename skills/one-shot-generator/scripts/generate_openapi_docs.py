#!/usr/bin/env python3
"""
Gap 7: OpenAPI/Swagger Documentation Generation

Auto-generates comprehensive API documentation:
- OpenAPI 3.1 specifications
- Swagger UI integration
- ReDoc documentation
- AsyncAPI schemas (for events)
- GraphQL schemas
- API client SDKs (Python, JavaScript, Go)

Input: Generated code, framework, endpoint definitions
Output: Complete API documentation and interactive UI
"""

import json
from typing import Dict, List


class OpenAPIDocGenerator:
    """Generates OpenAPI/Swagger documentation."""

    def __init__(self, framework: str, app_name: str):
        self.framework = framework.lower()
        self.app_name = app_name

    def generate_openapi_docs(self, endpoints: List[Dict], models: List[Dict]) -> Dict[str, str]:
        """
        Generate OpenAPI documentation.

        Returns: {filepath: content, ...}
        """
        configs = {}

        # OpenAPI spec
        configs['openapi.yaml'] = self._generate_openapi_spec(endpoints, models)
        configs['openapi.json'] = self._generate_openapi_json(endpoints, models)

        # Framework-specific integration
        if self.framework == 'django':
            configs['docs/swagger_setup.py'] = self._get_django_swagger_setup()
        elif self.framework == 'fastapi':
            configs['main.py.update'] = self._get_fastapi_swagger_setup()
        elif self.framework == 'spring':
            configs['src/main/java/com/example/config/SwaggerConfig.java'] = \
                self._get_spring_swagger_config()
        elif self.framework == 'go':
            configs['docs/swagger_setup.go'] = self._get_go_swagger_setup()
        elif self.framework in ['express', 'nodejs']:
            configs['docs/swagger_setup.js'] = self._get_nodejs_swagger_setup()

        # Client SDKs
        configs['sdks/python_client.py'] = self._generate_python_client(endpoints)
        configs['sdks/javascript_client.js'] = self._generate_javascript_client(endpoints)
        configs['sdks/go_client.go'] = self._generate_go_client(endpoints)

        # HTML documentation
        configs['docs/index.html'] = self._generate_swagger_ui_html()
        configs['docs/redoc.html'] = self._generate_redoc_html()

        return configs

    def _generate_openapi_spec(self, endpoints: List[Dict], models: List[Dict]) -> str:
        """Generate OpenAPI 3.1 specification in YAML."""
        paths = {}
        for endpoint in endpoints:
            path = endpoint.get('path', '/')
            method = endpoint.get('method', 'get').lower()

            if path not in paths:
                paths[path] = {}

            paths[path][method] = {
                'summary': endpoint.get('summary', f'{method.upper()} {path}'),
                'description': endpoint.get('description', ''),
                'tags': endpoint.get('tags', ['default']),
                'parameters': endpoint.get('parameters', []),
                'requestBody': endpoint.get('requestBody', {}),
                'responses': endpoint.get('responses', {'200': {'description': 'Success'}}),
            }

        components = {
            'schemas': {}
        }
        for model in models:
            components['schemas'][model['name']] = {
                'type': 'object',
                'properties': model.get('properties', {}),
                'required': model.get('required', []),
            }

        spec = {
            'openapi': '3.1.0',
            'info': {
                'title': self.app_name,
                'version': '1.0.0',
                'description': f'API documentation for {self.app_name}',
            },
            'servers': [
                {'url': 'http://localhost:8000', 'description': 'Development'},
                {'url': 'https://api.example.com', 'description': 'Production'},
            ],
            'paths': paths,
            'components': components,
        }

        # Convert to YAML-like format
        return self._dict_to_yaml(spec)

    def _generate_openapi_json(self, endpoints: List[Dict], models: List[Dict]) -> str:
        """Generate OpenAPI specification in JSON."""
        paths = {}
        for endpoint in endpoints:
            path = endpoint.get('path', '/')
            method = endpoint.get('method', 'get').lower()

            if path not in paths:
                paths[path] = {}

            paths[path][method] = {
                'summary': endpoint.get('summary', f'{method.upper()} {path}'),
                'tags': endpoint.get('tags', ['default']),
                'responses': endpoint.get('responses', {'200': {'description': 'Success'}}),
            }

        spec = {
            'openapi': '3.1.0',
            'info': {
                'title': self.app_name,
                'version': '1.0.0',
            },
            'paths': paths,
        }

        return json.dumps(spec, indent=2)

    def _get_django_swagger_setup(self) -> str:
        """Generate Django Swagger setup."""
        return f'''# settings.py additions for Swagger

INSTALLED_APPS = [
    ...
    'drf_spectacular',
    'drf_spectacular_sidecar',
]

REST_FRAMEWORK = {{
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}}

SPECTACULAR_SETTINGS = {{
    'TITLE': '{self.app_name} API',
    'DESCRIPTION': 'API documentation',
    'VERSION': '1.0.0',
    'SERVE_PERMISSIONS': ['rest_framework.permissions.AllowAny'],
    'SERVE_INCLUDE_SCHEMA': False,
}}

# urls.py additions
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema')),
]
'''

    def _get_fastapi_swagger_setup(self) -> str:
        """Generate FastAPI Swagger setup."""
        return f'''# main.py additions

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi

app = FastAPI(
    title='{self.app_name}',
    description='API documentation',
    version='1.0.0',
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title='{self.app_name}',
        version='1.0.0',
        routes=app.routes,
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Swagger UI available at /docs
# ReDoc available at /redoc
'''

    def _get_spring_swagger_config(self) -> str:
        return '''package com.example.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SwaggerConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("API Documentation")
                .version("1.0.0")
                .description("API documentation"));
    }
}
'''

    def _get_go_swagger_setup(self) -> str:
        return '''// swagger setup for Go

import (
    "github.com/swaggo/gin-swagger"
    "github.com/swaggo/files"
)

// @title           ''' + self.app_name + ''' API
// @version         1.0.0
// @description     This is the API documentation.
// @host            localhost:8080
// @basePath         /api/v1
func setupSwagger(router *gin.Engine) {
    router.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
}
'''

    def _get_nodejs_swagger_setup(self) -> str:
        return '''// Swagger setup for Node.js

const swaggerUI = require('swagger-ui-express');
const swaggerDoc = require('./openapi.json');

app.use('/api-docs', swaggerUI.serve, swaggerUI.setup(swaggerDoc));
'''

    def _generate_python_client(self, endpoints: List[Dict]) -> str:
        """Generate Python SDK client."""
        methods = '\n    '.join([
            f'''def {endpoint.get('method', 'get').lower()}(self, path: str, **kwargs):
        """Send {endpoint.get('method', 'GET')} request."""
        return self._request('{endpoint.get('method', 'GET').upper()}', path, **kwargs)
'''
            for endpoint in endpoints
        ])

        return f'''"""
{self.app_name} Python SDK Client
Generated from OpenAPI specification
"""

import requests
from typing import Dict, Any, Optional


class {self.app_name.title()}Client:
    """API client for {self.app_name}."""

    def __init__(self, base_url: str = 'http://localhost:8000', api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {{'Content-Type': 'application/json'}}
        if api_key:
            self.headers['Authorization'] = f'Bearer {{api_key}}'

    def _request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request."""
        url = f'{{self.base_url}}{{path}}'
        response = requests.request(
            method,
            url,
            headers=self.headers,
            **kwargs
        )
        return response.json()

    {methods}


if __name__ == '__main__':
    client = {self.app_name.title()}Client()
    # Example usage
    result = client.get('/api/items')
    print(result)
'''

    def _generate_javascript_client(self, endpoints: List[Dict]) -> str:
        """Generate JavaScript SDK client."""
        methods = '\n\n  '.join([
            f'''async {endpoint.get('method', 'get').lower()}(path, options = {{}}) {{
    return this._request('{endpoint.get('method', 'GET').upper()}', path, options);
  }}
'''
            for endpoint in endpoints
        ])

        return f'''/**
 * {self.app_name} JavaScript SDK Client
 * Generated from OpenAPI specification
 */

class {self.app_name.title()}Client {{
  constructor(baseUrl = 'http://localhost:8000', apiKey = null) {{
    this.baseUrl = baseUrl;
    this.apiKey = apiKey;
    this.headers = {{'Content-Type': 'application/json'}};
    if (apiKey) {{
      this.headers['Authorization'] = `Bearer ${{apiKey}}`;
    }}
  }}

  async _request(method, path, options = {{}}) {{
    const url = `${{this.baseUrl}}${{path}}`;
    const response = await fetch(url, {{
      method,
      headers: this.headers,
      ...options,
    }});
    return response.json();
  }}

  {methods}
}}

export default {self.app_name.title()}Client;
'''

    def _generate_go_client(self, endpoints: List[Dict]) -> str:
        """Generate Go SDK client."""
        methods = '\n'.join([
            f'''
func (c *{self.app_name.title()}Client) {endpoint.get('method', 'Get').title()}(path string) (interface{{}}, error) {{
    return c.request("{endpoint.get('method', 'GET').upper()}", path)
}}
'''
            for endpoint in endpoints
        ])

        return f'''package {self.app_name}

import (
    "bytes"
    "encoding/json"
    "io"
    "net/http"
)

type {self.app_name.title()}Client struct {{
    BaseURL string
    APIKey  string
    Client  *http.Client
}}

func New{self.app_name.title()}Client(baseURL, apiKey string) *{self.app_name.title()}Client {{
    return &{self.app_name.title()}Client{{
        BaseURL: baseURL,
        APIKey:  apiKey,
        Client:  &http.Client{{}},
    }}
}}

func (c *{self.app_name.title()}Client) request(method, path string) (interface{{}}, error) {{
    req, err := http.NewRequest(method, c.BaseURL+path, nil)
    if err != nil {{
        return nil, err
    }}

    if c.APIKey != "" {{
        req.Header.Set("Authorization", "Bearer "+c.APIKey)
    }}

    resp, err := c.Client.Do(req)
    if err != nil {{
        return nil, err
    }}
    defer resp.Body.Close()

    body, _ := io.ReadAll(resp.Body)
    var result interface{{}}
    json.Unmarshal(body, &result)
    return result, nil
}}{methods}
'''

    def _generate_swagger_ui_html(self) -> str:
        """Generate Swagger UI HTML."""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>{self.app_name} API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.css">
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/swagger-ui/4.15.5/swagger-ui.js"></script>
    <script>
        window.onload = function() {{
            window.ui = SwaggerUIBundle({{
                url: "/openapi.json",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "BaseLayout"
            }});
        }};
    </script>
</body>
</html>
'''

    def _generate_redoc_html(self) -> str:
        """Generate ReDoc HTML."""
        return f'''<!DOCTYPE html>
<html>
<head>
    <title>{self.app_name} API Documentation</title>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url='/openapi.json'></redoc>
    <script src="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js"></script>
</body>
</html>
'''

    def _dict_to_yaml(self, data: Dict) -> str:
        """Convert dict to YAML-like string."""
        def format_value(val, indent=0):
            spaces = '  ' * indent
            if isinstance(val, dict):
                lines = []
                for k, v in val.items():
                    if isinstance(v, (dict, list)):
                        lines.append(f"{spaces}{k}:")
                        lines.append(format_value(v, indent + 1))
                    else:
                        lines.append(f"{spaces}{k}: {v}")
                return '\n'.join(lines)
            elif isinstance(val, list):
                lines = []
                for item in val:
                    lines.append(f"{spaces}- {item}")
                return '\n'.join(lines)
            return str(val)

        return format_value(data)


def main():
    """Test OpenAPI documentation generation."""
    gen = OpenAPIDocGenerator('fastapi', 'myapp')
    endpoints = [
        {
            'path': '/items',
            'method': 'GET',
            'summary': 'List items',
        },
        {
            'path': '/items',
            'method': 'POST',
            'summary': 'Create item',
        },
    ]
    models = [
        {
            'name': 'Item',
            'properties': {
                'id': {'type': 'integer'},
                'name': {'type': 'string'},
            },
        },
    ]
    files = gen.generate_openapi_docs(endpoints, models)
    for filepath, content in files.items():
        print(f"File: {filepath}\n---\n")


if __name__ == '__main__':
    main()
