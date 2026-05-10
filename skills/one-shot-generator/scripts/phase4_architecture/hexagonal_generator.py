#!/usr/bin/env python3
"""Hexagonal Generator - Ports & Adapters (Ports & Adapters)

Generates:
- Ports (interfaces defining requirements)
- Adapters (implementations of ports)
- Anti-corruption layer (protect domain from external)
- Dependency inversion setup
"""

import sys
from pathlib import Path
from typing import Dict

sys.path.insert(0, str(Path(__file__).parent.parent))
from lib.base_script import setup_logging, timed_run, check_budget

__version__ = "0.7.0"
logger = setup_logging(__name__)


class HexagonalGenerator:
    """Generates hexagonal architecture patterns."""

    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['hexagonal/ports.py'] = self._ports()
        files['hexagonal/adapters.py'] = self._adapters()
        files['hexagonal/anti_corruption.py'] = self._anti_corruption()
        files['hexagonal/application.py'] = self._application()
        files['hexagonal/README.md'] = self._readme()
        return files

    def _ports(self) -> str:
        return '''"""Ports - Define Domain Requirements"""

from abc import ABC, abstractmethod
from typing import List, Optional, Any


class UserRepository(ABC):
    """Port: User persistence"""

    @abstractmethod
    def save(self, user: 'User') -> None:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Optional['User']:
        pass

    @abstractmethod
    def get_by_email(self, email: str) -> Optional['User']:
        pass

    @abstractmethod
    def delete(self, user_id: str) -> None:
        pass

    @abstractmethod
    def list_all(self) -> List['User']:
        pass


class EmailService(ABC):
    """Port: Send emails"""

    @abstractmethod
    def send_welcome_email(self, email: str, name: str) -> bool:
        pass

    @abstractmethod
    def send_password_reset(self, email: str, reset_token: str) -> bool:
        pass

    @abstractmethod
    def send_notification(self, email: str, message: str) -> bool:
        pass


class AuthenticationPort(ABC):
    """Port: External authentication"""

    @abstractmethod
    def verify_credentials(self, username: str, password: str) -> bool:
        pass

    @abstractmethod
    def hash_password(self, password: str) -> str:
        pass

    @abstractmethod
    def verify_password(self, password: str, hash: str) -> bool:
        pass


class PaymentPort(ABC):
    """Port: Process payments"""

    @abstractmethod
    def charge(self, customer_id: str, amount: float) -> str:
        """Returns transaction ID"""
        pass

    @abstractmethod
    def refund(self, transaction_id: str) -> bool:
        pass

    @abstractmethod
    def verify_payment(self, transaction_id: str) -> bool:
        pass


class LoggingPort(ABC):
    """Port: Logging abstraction"""

    @abstractmethod
    def log_info(self, message: str) -> None:
        pass

    @abstractmethod
    def log_error(self, message: str) -> None:
        pass

    @abstractmethod
    def log_warning(self, message: str) -> None:
        pass
'''

    def _adapters(self) -> str:
        return '''"""Adapters - Implement Ports"""

from typing import List, Optional
from abc import ABC


class InMemoryUserRepository(ABC):
    """Adapter: In-memory user storage"""

    def __init__(self):
        self.users = {}

    def save(self, user) -> None:
        self.users[user.id] = user

    def get_by_id(self, user_id: str) -> Optional[object]:
        return self.users.get(user_id)

    def get_by_email(self, email: str) -> Optional[object]:
        for user in self.users.values():
            if user.email == email:
                return user
        return None

    def delete(self, user_id: str) -> None:
        self.users.pop(user_id, None)

    def list_all(self) -> List[object]:
        return list(self.users.values())


class SQLUserRepository(ABC):
    """Adapter: SQL database user storage"""

    def __init__(self, db_connection):
        self.db = db_connection

    def save(self, user) -> None:
        query = "INSERT INTO users VALUES (?, ?, ?, ?)"
        self.db.execute(query, (user.id, user.email, user.name, user.password_hash))

    def get_by_id(self, user_id: str) -> Optional[object]:
        query = "SELECT * FROM users WHERE id = ?"
        return self.db.fetch_one(query, (user_id,))

    def get_by_email(self, email: str) -> Optional[object]:
        query = "SELECT * FROM users WHERE email = ?"
        return self.db.fetch_one(query, (email,))

    def delete(self, user_id: str) -> None:
        query = "DELETE FROM users WHERE id = ?"
        self.db.execute(query, (user_id,))

    def list_all(self) -> List[object]:
        query = "SELECT * FROM users"
        return self.db.fetch_all(query)


class SMTPEmailAdapter(ABC):
    """Adapter: Send emails via SMTP"""

    def __init__(self, smtp_host: str, smtp_port: int, sender_email: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email

    def send_welcome_email(self, email: str, name: str) -> bool:
        # Implementation using SMTP
        return True

    def send_password_reset(self, email: str, reset_token: str) -> bool:
        # Implementation
        return True

    def send_notification(self, email: str, message: str) -> bool:
        # Implementation
        return True


class StripePaymentAdapter(ABC):
    """Adapter: Stripe payment processing"""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def charge(self, customer_id: str, amount: float) -> str:
        # Call Stripe API
        return "transaction-123"

    def refund(self, transaction_id: str) -> bool:
        # Call Stripe API
        return True

    def verify_payment(self, transaction_id: str) -> bool:
        # Call Stripe API
        return True


class StandardLoggingAdapter(ABC):
    """Adapter: Standard Python logging"""

    def __init__(self, logger):
        self.logger = logger

    def log_info(self, message: str) -> None:
        self.logger.info(message)

    def log_error(self, message: str) -> None:
        self.logger.error(message)

    def log_warning(self, message: str) -> None:
        self.logger.warning(message)
'''

    def _anti_corruption(self) -> str:
        return '''"""Anti-Corruption Layer - Translate External to Internal"""

from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)


class ExternalUserDTO:
    """External user representation (from third-party API)"""

    def __init__(self, data: Dict[str, Any]):
        self.external_id = data.get("user_id")
        self.external_email = data.get("email_address")
        self.external_name = data.get("full_name")
        self.external_status = data.get("status")


class UserAntiCorruptionLayer:
    """Translate external user format to internal domain"""

    @staticmethod
    def translate_external_user(external_dto: ExternalUserDTO) -> 'User':
        """Convert external DTO to domain User"""
        logger.info(f"Translating external user {external_dto.external_id}")

        # Domain logic: validate and transform
        user = User(
            id=external_dto.external_id,
            email=external_dto.external_email,
            name=external_dto.external_name,
            is_active=(external_dto.external_status == "ACTIVE")
        )

        return user

    @staticmethod
    def translate_to_external(user: 'User') -> Dict[str, Any]:
        """Convert domain User to external format"""
        return {
            "user_id": user.id,
            "email_address": user.email,
            "full_name": user.name,
            "status": "ACTIVE" if user.is_active else "INACTIVE"
        }


class PaymentAntiCorruptionLayer:
    """Translate Stripe response to domain"""

    @staticmethod
    def translate_stripe_response(stripe_response: Dict[str, Any]) -> 'Payment':
        """Convert Stripe response to domain Payment"""
        logger.info(f"Translating Stripe response {stripe_response.get('id')}")

        payment = Payment(
            transaction_id=stripe_response.get("id"),
            amount=stripe_response.get("amount") / 100,  # Stripe uses cents
            currency=stripe_response.get("currency").upper(),
            status=stripe_response.get("status"),
            customer_id=stripe_response.get("customer")
        )

        return payment


class ExternalServiceAdapter:
    """Generic adapter for external services"""

    def __init__(self, external_service, anti_corruption_layer):
        self.external_service = external_service
        self.anti_corruption_layer = anti_corruption_layer

    def call_external_service(self, method_name: str, *args, **kwargs) -> Any:
        """Call external service and translate response"""
        logger.info(f"Calling external service: {method_name}")

        # Call external service
        response = getattr(self.external_service, method_name)(*args, **kwargs)

        # Translate response through anti-corruption layer
        translated = self.anti_corruption_layer.translate(response)

        return translated
'''

    def _application(self) -> str:
        return '''"""Application - Wires Up Ports & Adapters"""

import logging

logger = logging.getLogger(__name__)


class ApplicationConfiguration:
    """Configures application with ports and adapters"""

    def __init__(self):
        self.ports = {}
        self.adapters = {}

    def register_port(self, port_name: str, port_interface):
        """Register port"""
        self.ports[port_name] = port_interface
        logger.info(f"Registered port: {port_name}")

    def register_adapter(self, adapter_name: str, adapter_impl):
        """Register adapter for port"""
        self.adapters[adapter_name] = adapter_impl
        logger.info(f"Registered adapter: {adapter_name}")

    def get_adapter(self, port_name: str):
        """Get adapter for port"""
        if port_name not in self.adapters:
            raise ValueError(f"No adapter for {port_name}")
        return self.adapters[port_name]

    def wire_up(self):
        """Wire up all ports and adapters"""
        logger.info("Wiring up ports and adapters")
        # This is where dependency injection happens
        return self


class ApplicationBootstrapper:
    """Bootstrap application with dependency injection"""

    @staticmethod
    def create_app():
        """Create and configure application"""
        config = ApplicationConfiguration()

        # Register ports
        config.register_port("UserRepository", None)
        config.register_port("EmailService", None)
        config.register_port("PaymentService", None)
        config.register_port("AuthService", None)

        # Register adapters
        config.register_adapter("UserRepository", InMemoryUserRepository())
        config.register_adapter("EmailService", SMTPEmailAdapter("localhost", 25, "noreply@example.com"))
        config.register_adapter("PaymentService", StripePaymentAdapter("sk_test_..."))
        config.register_adapter("AuthService", StandardAuthAdapter())

        config.wire_up()

        logger.info("Application bootstrapped")
        return config
'''

    def _readme(self) -> str:
        return '''# Hexagonal Architecture - Ports & Adapters

## Core Concept

Isolate domain logic from external dependencies:

```
          User Interface
              │
         [Adapter]
              │
    ┌─────────┴─────────┐
    │   DOMAIN LOGIC    │
    │   (Application)   │
    └─────────┬─────────┘
              │
         [Adapter]
              │
        External System
```

## Ports

Interfaces defining what domain needs:

```python
from hexagonal.ports import UserRepository, EmailService, PaymentPort

class UserRepository(ABC):
    @abstractmethod
    def save(self, user): pass

    @abstractmethod
    def get_by_id(self, user_id): pass
```

Domain doesn't care HOW data persists, only that it can save/retrieve.

## Adapters

Implementations of ports:

```python
from hexagonal.adapters import InMemoryUserRepository, SQLUserRepository

# For testing
repo = InMemoryUserRepository()

# For production
repo = SQLUserRepository(db_connection)

# Both satisfy UserRepository interface
```

## Anti-Corruption Layer

Translate external formats to domain:

```python
from hexagonal.anti_corruption import UserAntiCorruptionLayer

# External API returns different format
external_user = third_party_api.get_user(user_id)

# Translate to domain format
user = UserAntiCorruptionLayer.translate_external_user(external_user)
```

Protects domain from external API changes.

## Dependency Injection

Wire up at bootstrap:

```python
from hexagonal.application import ApplicationBootstrapper

config = ApplicationBootstrapper.create_app()

# Config now has all adapters ready
user_repo = config.get_adapter("UserRepository")
email_service = config.get_adapter("EmailService")
```

## Benefits

1. **Testability**: Swap real adapters with test doubles
2. **Flexibility**: Change implementations without changing domain
3. **Independence**: Domain is independent of frameworks
4. **Portability**: Move to different database, email provider, etc.

## Typical Structure

```
src/
├── domain/              # Business logic
│   ├── user.py
│   ├── order.py
│   └── payment.py
│
├── ports/              # Interfaces
│   ├── user_repository.py
│   ├── email_service.py
│   └── payment_service.py
│
├── adapters/           # Implementations
│   ├── sql_user_repo.py
│   ├── smtp_email.py
│   └── stripe_payment.py
│
├── anti_corruption/    # Translation layers
│   ├── external_user_translator.py
│   └── stripe_translator.py
│
└── application.py      # Dependency injection
```

## Example: User Registration

```python
# Port (what domain needs)
class UserRepository(ABC):
    def save(self, user): pass

# Adapter (implementation)
class SQLUserRepository(UserRepository):
    def save(self, user):
        # SQL logic

# Domain (doesn't care about SQL)
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def register_user(self, email, password):
        user = User(email, password)
        self.user_repo.save(user)

# Wire up
repo = SQLUserRepository(db)
service = UserService(repo)
service.register_user("user@example.com", "password123")

# Testing: swap adapter
test_repo = InMemoryUserRepository()
service = UserService(test_repo)
service.register_user("test@example.com", "password")
```

## Key Principle

**Depend on abstractions (ports), not concretions (adapters).**
'''


def main():
    with timed_run("hexagonal_generator") as timer:
        logger.debug("Testing Hexagonal generation")
        gen = HexagonalGenerator("python")
        files = gen.generate()
        logger.debug(f"Generated {len(files)} Hexagonal files")
        for filepath in files:
            print(f"  ✓ {filepath}")
        check_budget("hexagonal_generator", timer.elapsed_ms, logger)


if __name__ == '__main__':
    main()
