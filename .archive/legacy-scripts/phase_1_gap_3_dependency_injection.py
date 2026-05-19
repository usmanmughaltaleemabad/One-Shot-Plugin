#!/usr/bin/env python3
"""
Generate dependency injection container and service registration.

Supports Django, FastAPI, NestJS, Express, Spring patterns.
"""

from typing import Dict, List, Set


class DependencyInjectionGenerator:
    """Generate DI container and service registration."""

    def __init__(self, framework: str):
        self.framework = framework.lower()
        self.services: Dict[str, List[str]] = {}  # service -> dependencies

    def add_service(self, service_name: str, dependencies: List[str] = None) -> None:
        """Register a service with its dependencies."""
        self.services[service_name] = dependencies or []

    def detect_cycles(self) -> List[List[str]]:
        """Detect circular dependencies."""
        cycles = []

        def dfs(node, path, visited):
            if node in path:
                cycle_start = path.index(node)
                cycles.append(path[cycle_start:] + [node])
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for dep in self.services.get(node, []):
                dfs(dep, path[:], visited.copy())

        for service in self.services:
            dfs(service, [], set())

        return cycles

    def generate_django(self) -> str:
        """Generate Django dependency injection setup."""
        code = '''# Dependency Injection Container (Django)

class DIContainer:
    """Service container for dependency injection."""

    def __init__(self):
        self._services = {}
        self._singletons = {}

    def register(self, name: str, factory):
        """Register a service factory."""
        self._services[name] = factory

    def get(self, name: str):
        """Get service instance (singleton)."""
        if name not in self._singletons:
            factory = self._services.get(name)
            if not factory:
                raise ValueError(f"Service {name} not registered")
            self._singletons[name] = factory()
        return self._singletons[name]

# Global container instance
container = DIContainer()

# Service registration
'''

        for service_name, deps in self.services.items():
            if deps:
                code += f'# container.register("{service_name}", lambda: {service_name}({", ".join(["container.get(\"" + d + "\")" for d in deps])}))\n'
            else:
                code += f'# container.register("{service_name}", lambda: {service_name}())\n'

        return code

    def generate_fastapi(self) -> str:
        """Generate FastAPI dependency injection setup."""
        code = '''# Dependency Injection (FastAPI with Depends)

from fastapi import Depends

def get_db():
    """Database dependency."""
    # Return database connection
    pass

def get_cache():
    """Cache dependency."""
    # Return cache client
    pass

# Service dependencies
'''

        for service_name, deps in self.services.items():
            if deps:
                code += f'''
async def get_{service_name.lower()}({", ".join([f"{d}_dep = Depends(get_{d.lower()})" for d in deps])}) -> {service_name}:
    """Provide {service_name} with injected dependencies."""
    return {service_name}({", ".join(deps)})
'''
            else:
                code += f'''
def get_{service_name.lower()}() -> {service_name}:
    """Provide {service_name}."""
    return {service_name}()
'''

        return code

    def generate_nestjs(self) -> str:
        """Generate NestJS module and provider setup."""
        code = '''// Dependency Injection (NestJS)

import { Module, Injectable } from '@nestjs/common';

// Services
'''

        for service_name, deps in self.services.items():
            code += f'''
@Injectable()
export class {service_name} {{
  constructor(
'''
            for i, dep in enumerate(deps):
                code += f'    private readonly {dep.lower()}: {dep},\n'
            code += '  ) {}\n}\n'

        code += '''
@Module({
  providers: [
'''
        for service_name in self.services:
            code += f'    {service_name},\n'
        code += '  ],\n  exports: [' + ', '.join(self.services.keys()) + '],\n})\nexport class ServicesModule {}\n'

        return code

    def generate_express(self) -> str:
        """Generate Express manual DI setup."""
        code = '''// Dependency Injection (Express - Manual Factory Pattern)

class DIContainer {
  constructor() {
    this.services = {};
  }

  register(name, factory) {
    this.services[name] = factory;
  }

  get(name) {
    const factory = this.services[name];
    if (!factory) throw new Error(`Service ${name} not found`);
    return factory();
  }
}

const container = new DIContainer();

// Service registration
'''

        for service_name, deps in self.services.items():
            if deps:
                dep_calls = ', '.join([f'container.get("{d}")' for d in deps])
                code += f'container.register("{service_name}", () => new {service_name}({dep_calls}));\n'
            else:
                code += f'container.register("{service_name}", () => new {service_name}());\n'

        return code

    def generate_spring(self) -> str:
        """Generate Spring configuration class."""
        code = '''// Dependency Injection (Spring with @Configuration)

package com.example.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class DIConfiguration {

  // Bean definitions
'''

        for service_name, deps in self.services.items():
            if deps:
                params = ', '.join([f'{d.lower()} {d}' for d in deps])
                code += f'''
  @Bean
  public {service_name} {service_name.lower()}({params}) {{
    return new {service_name}({", ".join([d.lower() for d in deps])});
  }}
'''
            else:
                code += f'''
  @Bean
  public {service_name} {service_name.lower()}() {{
    return new {service_name}();
  }}
'''

        code += '}\n'
        return code

    def generate(self) -> str:
        """Generate DI code for framework."""
        if self.framework == 'django':
            return self.generate_django()
        elif self.framework == 'fastapi':
            return self.generate_fastapi()
        elif self.framework == 'nestjs':
            return self.generate_nestjs()
        elif self.framework == 'express':
            return self.generate_express()
        elif self.framework == 'spring':
            return self.generate_spring()
        else:
            return '# Dependency Injection\n'


def generate_dependency_injection(
    framework: str,
    services: Dict[str, List[str]]
) -> str:
    """Generate dependency injection setup."""
    generator = DependencyInjectionGenerator(framework)

    for service_name, deps in services.items():
        generator.add_service(service_name, deps)

    # Check for cycles
    cycles = generator.detect_cycles()
    if cycles:
        raise ValueError(f"Circular dependencies detected: {cycles}")

    return generator.generate()
