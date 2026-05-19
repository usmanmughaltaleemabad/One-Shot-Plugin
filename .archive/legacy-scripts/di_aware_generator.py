#!/usr/bin/env python3
"""
Gap 5: Dependency Injection (DI)-Aware Generation

Detects and wraps services/controllers with proper DI annotations:
- Spring Boot: @Service, @Autowired constructor injection, @Component
- FastAPI: Depends() provider function generation
- Go: wire.Build() provider set, interface-based injection
- NestJS: @Injectable(), @InjectRepository(), @Module() setup

Input: Service code, detected DI pattern, framework
Output: DI-annotated service + provider setup + module registration
"""

import sys
import re
from typing import Dict, Optional, Tuple
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class DIAwareGenerator:
    """Detects DI pattern and wraps code with proper annotations."""

    # DI pattern detection signatures
    DI_SIGNATURES = {
        'spring': [
            'org.springframework.stereotype.Service',
            'org.springframework.beans.factory.annotation.Autowired',
            '@Autowired',
            '@Service',
        ],
        'fastapi': [
            'from fastapi import Depends',
            'Depends(',
            'def get_',
        ],
        'nestjs': [
            'Injectable',
            '@Module',
            '@Inject',
            'NestFactory',
        ],
        'go': [
            'wire.Build',
            'wire.Struct',
            'google.golang.org/wire',
        ],
    }

    def __init__(self, framework: str, language: str = 'auto'):
        self.framework = framework.lower()
        self.language = language.lower() if language != 'auto' else self._infer_language()

    def detect_di_pattern(self, codebase_sample: str) -> Optional[str]:
        """Detect DI pattern used in codebase."""
        for pattern, signatures in self.DI_SIGNATURES.items():
            if any(sig in codebase_sample for sig in signatures):
                return pattern
        return None

    def wrap_service(self, service_code: str, service_name: str, di_pattern: Optional[str] = None) -> str:
        """
        Wrap service with DI annotations.

        Args:
            service_code: Original service class code
            service_name: Service class name
            di_pattern: Detected DI pattern (auto-detected if None)

        Returns:
            DI-annotated service code
        """
        if not di_pattern:
            di_pattern = 'spring'  # Default to Spring

        if self.framework == 'spring' or di_pattern == 'spring':
            return self._wrap_spring_service(service_code, service_name)
        elif self.framework == 'fastapi' or di_pattern == 'fastapi':
            return self._wrap_fastapi_service(service_code, service_name)
        elif self.framework == 'nestjs' or di_pattern == 'nestjs':
            return self._wrap_nestjs_service(service_code, service_name)
        elif self.framework == 'go' or di_pattern == 'go':
            return self._wrap_go_service(service_code, service_name)
        else:
            return service_code

    def wrap_controller(self, controller_code: str, controller_name: str, dependencies: Dict[str, str],
                      di_pattern: Optional[str] = None) -> str:
        """
        Wrap controller with DI-aware dependency injection.

        Args:
            controller_code: Original controller code
            controller_name: Controller class name
            dependencies: Dict mapping {service_field: ServiceClass}
            di_pattern: Detected DI pattern

        Returns:
            DI-annotated controller code
        """
        if not di_pattern:
            di_pattern = 'spring'

        if self.framework == 'spring' or di_pattern == 'spring':
            return self._wrap_spring_controller(controller_code, controller_name, dependencies)
        elif self.framework == 'fastapi' or di_pattern == 'fastapi':
            return self._wrap_fastapi_route(controller_code, controller_name, dependencies)
        elif self.framework == 'nestjs' or di_pattern == 'nestjs':
            return self._wrap_nestjs_controller(controller_code, controller_name, dependencies)
        elif self.framework == 'go' or di_pattern == 'go':
            return self._wrap_go_handler(controller_code, controller_name, dependencies)
        else:
            return controller_code

    def _wrap_spring_service(self, code: str, service_name: str) -> str:
        """Add Spring @Service, @Autowired annotations."""
        # Check if @Service already exists
        if '@Service' in code:
            return code

        # Add @Service annotation
        imports = '@Service\npublic class' if 'import' not in code else ''

        if code.startswith('public class'):
            code = f"@Service\n{code}"

        # Ensure Spring imports
        spring_imports = '''import org.springframework.stereotype.Service;
import org.springframework.beans.factory.annotation.Autowired;
'''

        if 'import org.springframework' not in code:
            code = spring_imports + '\n' + code

        # Add @Autowired to constructor parameters
        # TODO: More sophisticated constructor detection
        return code

    def _wrap_spring_controller(self, code: str, name: str, deps: Dict[str, str]) -> str:
        """Add Spring @RestController, @Autowired injection."""
        if '@RestController' in code:
            return code

        code = f"@RestController\n{code}"

        # Add @Autowired fields
        for field_name, service_class in deps.items():
            autowired_field = f"    @Autowired\n    private {service_class} {field_name};"
            # Insert before first method
            code = code.replace('    public', f"{autowired_field}\n\n    public", 1)

        return code

    def _wrap_fastapi_service(self, code: str, service_name: str) -> str:
        """Wrap FastAPI service with Depends() provider."""
        provider_code = f'''# Dependency provider for {service_name}
from fastapi import Depends


async def get_{service_name.lower()}() -> {service_name}:
    """Provides an instance of {service_name}"""
    return {service_name}()


# Usage in routes:
# @app.get("/endpoint")
# async def endpoint(service: {service_name} = Depends(get_{service_name.lower()})):
#     return await service.method()
'''

        return provider_code + '\n\n' + code

    def _wrap_fastapi_route(self, code: str, controller_name: str, deps: Dict[str, str]) -> str:
        """Add FastAPI Depends() injection to routes."""
        # Generate Depends() parameters
        depends_params = []
        for field_name, service_class in deps.items():
            depends_params.append(f"{field_name}: {service_class} = Depends(get_{field_name})")

        params_str = ', '.join(depends_params)

        # Inject into route signatures
        if '@app.' in code:
            # Add Depends to route
            code = re.sub(
                r'(async def \w+)\(',
                rf'\1({params_str}, ',
                code
            )

        return code

    def _wrap_nestjs_service(self, code: str, service_name: str) -> str:
        """Add NestJS @Injectable() decorator."""
        if '@Injectable' in code:
            return code

        code = f'''@Injectable()
{code}'''

        # Ensure NestJS imports
        if 'import { Injectable }' not in code:
            code = "import { Injectable } from '@nestjs/common';\n\n" + code

        return code

    def _wrap_nestjs_controller(self, code: str, controller_name: str, deps: Dict[str, str]) -> str:
        """Add NestJS @Controller, @Inject decorators."""
        if '@Controller' in code:
            return code

        code = f'''@Controller()
{code}'''

        # Add @Inject for each dependency
        for field_name, service_class in deps.items():
            inject_decorator = f'''    @Inject()
    private readonly {field_name}: {service_class};
'''
            # Insert before first method
            code = code.replace('    constructor', f"{inject_decorator}\n    constructor", 1)

        return code

    def _wrap_go_service(self, code: str, service_name: str) -> str:
        """Add Go wire.Build() provider setup."""
        provider_set = f'''package service

import "github.com/google/wire"

// {service_name}Set provides {service_name} and its dependencies
var {service_name}Set = wire.NewSet(
    New{service_name},
)

// New{service_name} creates a new instance of {service_name}
func New{service_name}() *{service_name} {{
    return &{service_name}{{}}
}}
'''

        return provider_set + '\n\n' + code

    def _wrap_go_handler(self, code: str, handler_name: str, deps: Dict[str, str]) -> str:
        """Add Go wire.FieldsOf() for handler injection."""
        deps_line = ', '.join(deps.values())

        wiring = f'''// Wire setup for {handler_name}
// In wire.go:
// var {handler_name}Set = wire.NewSet(
//     wire.FieldsOf(new({handler_name}), "Service1", "Service2"),
// )
'''

        return wiring + '\n\n' + code

    def _infer_language(self) -> str:
        """Infer language from framework."""
        framework_lang = {
            'spring': 'java',
            'fastapi': 'python',
            'nestjs': 'typescript',
            'go': 'go',
            'django': 'python',
            'express': 'javascript',
        }
        return framework_lang.get(self.framework, 'python')


def main():
    """Test DI-aware wrapping."""
    with timed_run("di_aware_generator") as timer:
        logger.debug("Testing DI-aware code wrapping")

        test_service = '''public class PaymentService {
    private PaymentRepository repo;
    private NotificationService notif;

    public void processPayment(Payment p) {
        // Process payment
    }
}
'''

        gen = DIAwareGenerator('spring')
        wrapped = gen.wrap_service(test_service, 'PaymentService')

        logger.debug("Generated Spring-annotated service")
        print(f"\n{'='*60}")
        print("Original Service:")
        print(test_service)
        print(f"{'='*60}")
        print("DI-Wrapped Service:")
        print(wrapped)

        check_budget("di_aware_generator", timer.elapsed_ms, logger)

    logger.debug(f"di_aware_generator completed in {timer.elapsed_ms:.0f}ms")


if __name__ == '__main__':
    main()
