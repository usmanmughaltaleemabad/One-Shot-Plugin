#!/usr/bin/env python3
"""
Phase 5 Security: Authentication & Authorization Patterns

Authentication: "Who are you?"
- Login with username/password
- Issue JWT token
- Token proves identity

Authorization: "Can you do this?"
- User is alice@company.com
- Can alice view customer #123 data?
- Yes: she's the sales rep assigned
- No: not assigned

Patterns:
- OAuth 2.0: social login (Google, GitHub)
- JWT: stateless tokens
- RBAC: role-based access (admin, user, guest)
- ABAC: attribute-based (user.department==sales AND resource.department==sales)
"""

from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta


def generate_auth_patterns() -> str:
    """Generate authentication patterns."""

    auth = '''
class AuthenticationManager:
    """
    Handle user authentication.

    Methods:
    - Username/password: traditional
    - JWT: stateless tokens
    - OAuth: delegated (social login)
    - SAML: enterprise (Active Directory)
    - MFA: multi-factor (password + SMS)
    """

    def __init__(self):
        self._users = {}  # user_id → {password_hash, ...}
        self._tokens = {}  # token → user_id

    def login(self, username: str, password: str) -> Optional[str]:
        """Authenticate and return token"""
        # Verify password (bcrypt or argon2)
        user = self._users.get(username)

        if not user:
            return None

        if not self._verify_password(password, user["password_hash"]):
            return None

        # Create JWT token
        token = self._create_jwt(username)
        self._tokens[token] = username

        return token

    def verify_token(self, token: str) -> Optional[str]:
        """Verify token and return user_id"""
        return self._tokens.get(token)

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        # In production: use bcrypt.checkpw()
        return True

    def _create_jwt(self, username: str) -> str:
        """Create JWT token"""
        # In production: use PyJWT with secret key
        return f"jwt_{username}_{datetime.utcnow().timestamp()}"
'''

    return auth


def generate_authorization() -> str:
    """Generate authorization patterns."""

    authz = '''
class AuthorizationManager:
    """
    Control who can do what.

    Patterns:
    - RBAC: user has roles (admin, editor, viewer)
    - ABAC: decisions based on attributes
    - ACL: explicit permission list
    """

    def __init__(self):
        self._roles = {}  # user_id → {roles}
        self._permissions = {}  # role → {permissions}
        self._acl = {}  # resource_id → {user_id: [permissions]}

    def assign_role(self, user_id: str, role: str) -> None:
        """Assign role to user"""
        if user_id not in self._roles:
            self._roles[user_id] = set()

        self._roles[user_id].add(role)

    def define_permissions(self, role: str, permissions: List[str]) -> None:
        """Define permissions for role"""
        self._permissions[role] = set(permissions)

    def can_user_perform(
        self,
        user_id: str,
        action: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """Check if user can perform action"""
        # Check RBAC
        user_roles = self._roles.get(user_id, set())

        for role in user_roles:
            perms = self._permissions.get(role, set())
            if action in perms:
                # Verify ACL if resource-specific
                if resource_id:
                    acl = self._acl.get(resource_id, {})
                    if user_id in acl and action in acl[user_id]:
                        return True
                else:
                    return True

        return False
'''

    return authz


def generate_security_system() -> dict:
    """Generate complete security system."""

    imports = '''from typing import Dict, Optional, List, Set
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 5 Security Patterns: Authentication & Authorization

Secure user access (OAuth2, JWT, RBAC).

AUTHENTICATION (who are you):

Method 1: Username/Password
- User enters: alice, password123
- Server: hash password, compare to stored hash
- Match: create token
- Issue: session or JWT token

Method 2: JWT (stateless)
- Token contains: {user_id, roles, expiration}
- Signed with secret key
- No session storage needed
- Ideal for distributed systems

Method 3: OAuth (social login)
- User: "Login with Google"
- Redirect to Google
- Google confirms identity
- Redirect back with code
- Exchange code for token

AUTHORIZATION (can you do this):

Role-Based Access Control (RBAC):
- User: alice
- Roles: admin, sales_rep
- Admin role: can_read_all_users, can_delete_user
- Sales_rep role: can_read_customer

Access Control List (ACL):
- Resource: customer_123_profile
- User alice: can_read, can_edit
- User bob: can_read only
- User charlie: no access

EXAMPLE: E-commerce

Authentication:
1. User logs in: alice@company.com / password
2. Server verifies password
3. Issues JWT: {user_id: alice, roles: [customer]}
4. Token valid for 1 week

Authorization:
- GET /customers/me → allowed (alice viewing her own profile)
- GET /customers/bob → denied (alice viewing someone else)
- GET /admin/users → denied (only admin role)

SECURITY BEST PRACTICES:

Passwords:
✓ Hash with bcrypt or argon2
✓ Use salt
✓ Never log passwords
✓ Require minimum length (12 characters)
✓ Force password reset every 90 days

Tokens:
✓ Use HTTPS only (token in Authorization header)
✓ Set expiration (JWT)
✓ Rotate regularly
✓ Revoke compromised tokens

MFA:
✓ Require password + SMS code
✓ Backup codes for recovery
✓ TOTP apps (Google Authenticator)
"""
'''

    auth = generate_auth_patterns()
    authz = generate_authorization()

    complete_code = imports + module_doc + "\n" + auth + "\n" + authz

    return {
        "code": complete_code,
        "pattern": "Security Patterns",
        "module": "phase5_security_patterns.py"
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate security patterns")
    args = parser.parse_args()
    result = generate_security_system()
    print(result["code"])


if __name__ == "__main__":
    main()
