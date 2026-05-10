"""
Permission Handler - Role-based access control (RBAC)

Generates permission checking logic for:
- Role-based access control (RBAC)
- Permission checking decorators
- Resource-level permissions
- Admin-only endpoints
- User ownership verification
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class Role(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


@dataclass
class Permission:
    """Permission definition"""
    name: str
    description: str
    roles: List[str]  # roles that have this permission


class PermissionGenerator:
    """Generate permission checking code"""

    def __init__(self, framework: str, resource_name: str):
        self.framework = framework
        self.resource_name = resource_name

    def generate_django(self) -> str:
        """Generate Django permission decorators"""
        return """
from functools import wraps
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.exceptions import PermissionDenied

class IsAdmin(BasePermission):
    message = 'Admin access required'

    def has_permission(self, request, view):
        return request.user and request.user.is_staff

class IsOwner(BasePermission):
    message = 'You do not own this object'

    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user.id

class HasRole(BasePermission):
    required_roles = []

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return self._user_has_role(request.user)

    def _user_has_role(self, user):
        user_roles = set(user.groups.values_list('name', flat=True))
        return bool(user_roles.intersection(set(self.required_roles)))

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in ['GET', 'HEAD', 'OPTIONS']

def require_permission(permission_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not check_user_permission(request.user, permission_name):
                raise PermissionDenied(f"Permission '{permission_name}' required")
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def require_role(role: str):
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            if not user_has_role(request.user, role):
                raise PermissionDenied(f"Role '{role}' required")
            return func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def is_owner(obj, user):
    return hasattr(obj, 'owner_id') and obj.owner_id == user.id

def user_has_role(user, role: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.groups.filter(name=role).exists()

def user_has_permission(user, permission: str) -> bool:
    if not user or not user.is_authenticated:
        return False
    return user.has_perm(permission)

def check_user_permission(user, permission: str) -> bool:
    return user_has_permission(user, permission)

class PermissionChecker:
    @staticmethod
    def check_list_permission(user, resource_name: str) -> bool:
        return user.has_perm(f'{resource_name}.view_{resource_name}')

    @staticmethod
    def check_create_permission(user, resource_name: str) -> bool:
        return user.has_perm(f'{resource_name}.add_{resource_name}')

    @staticmethod
    def check_update_permission(user, resource_name: str, obj) -> bool:
        if not user.has_perm(f'{resource_name}.change_{resource_name}'):
            return False
        return is_owner(obj, user) or user.is_staff

    @staticmethod
    def check_delete_permission(user, resource_name: str, obj) -> bool:
        if not user.has_perm(f'{resource_name}.delete_{resource_name}'):
            return False
        return is_owner(obj, user) or user.is_staff
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI permission checking"""
        return """
from fastapi import Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

class User(BaseModel):
    id: int
    username: str
    roles: List[str] = []

class Permission:
    def __init__(self, name: str, required_roles: List[str] = None):
        self.name = name
        self.required_roles = required_roles or ['admin']

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if not await self.check_permission(current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{self.name}' required"
            )
        return current_user

    async def check_permission(self, user: User) -> bool:
        if not self.required_roles:
            return user is not None
        return any(role in user.roles for role in self.required_roles)

class RoleRequired:
    def __init__(self, roles: List[str]):
        self.roles = roles

    async def __call__(self, current_user: User = Depends(get_current_user)):
        if not current_user or not any(role in current_user.roles for role in self.roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of these roles required: {', '.join(self.roles)}"
            )
        return current_user

class IsOwner:
    async def __call__(self, current_user: User = Depends(get_current_user), obj_id: int = None):
        if not current_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

        # Retrieve object and check ownership
        obj = await get_object(obj_id)
        if not obj or obj.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not own this resource"
            )
        return current_user

class IsAdmin:
    async def __call__(self, current_user: User = Depends(get_current_user)):
        if not current_user or 'admin' not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return current_user

async def get_current_user() -> Optional[User]:
    # Implementation from auth_handler.py
    pass

async def get_object(obj_id: int):
    # Retrieve object from database
    pass

def check_permission(user: User, permission: str) -> bool:
    # Simple permission check
    return user is not None

def user_has_role(user: User, role: str) -> bool:
    return role in (user.roles if user else [])

def user_owns_object(user: User, obj) -> bool:
    return hasattr(obj, 'owner_id') and obj.owner_id == user.id
"""


def generate_permission_code(
    framework: str,
    resource_name: str
) -> Dict[str, str]:
    """
    Generate permission checking code.

    Args:
        framework: django or fastapi
        resource_name: e.g., "user"

    Returns: dict of {filename: code_content}
    """
    generator = PermissionGenerator(framework, resource_name)
    output = {}

    if framework == "django":
        output["permissions.py"] = generator.generate_django()
    elif framework == "fastapi":
        output["permissions.py"] = generator.generate_fastapi()

    return output
