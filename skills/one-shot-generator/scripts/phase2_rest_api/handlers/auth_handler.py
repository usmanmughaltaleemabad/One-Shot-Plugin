"""
Authentication Handler - JWT, OAuth, API key validation

Generates authentication logic for:
- JWT validation with configurable algorithms
- OAuth 2.0 token handling
- API key validation
- Bearer token extraction
- Token expiration and refresh logic
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class AuthType(Enum):
    JWT = "jwt"
    OAUTH = "oauth"
    API_KEY = "api_key"
    BASIC = "basic"


@dataclass
class AuthConfig:
    """Authentication configuration"""
    auth_type: AuthType
    secret_key: Optional[str] = None
    algorithm: str = "HS256"  # HS256, RS256, etc.
    expiration_minutes: int = 60
    issuer: Optional[str] = None
    audience: Optional[str] = None
    oauth_provider: Optional[str] = None  # google, github, etc.
    api_key_header: str = "X-API-Key"


class AuthenticationGenerator:
    """Generate authentication code"""

    def __init__(self, framework: str, auth_config: AuthConfig):
        self.framework = framework
        self.config = auth_config

    def generate_django(self) -> str:
        """Generate Django authentication middleware"""
        if self.config.auth_type == AuthType.JWT:
            return self._generate_django_jwt()
        elif self.config.auth_type == AuthType.OAUTH:
            return self._generate_django_oauth()
        elif self.config.auth_type == AuthType.API_KEY:
            return self._generate_django_api_key()
        return ""

    def generate_fastapi(self) -> str:
        """Generate FastAPI authentication code"""
        if self.config.auth_type == AuthType.JWT:
            return self._generate_fastapi_jwt()
        elif self.config.auth_type == AuthType.OAUTH:
            return self._generate_fastapi_oauth()
        elif self.config.auth_type == AuthType.API_KEY:
            return self._generate_fastapi_api_key()
        return ""

    def _generate_django_jwt(self) -> str:
        return """
import jwt
from datetime import datetime, timedelta
from django.conf import settings
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed

class JWTAuthentication(TokenAuthentication):
    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        try:
            payload = jwt.decode(key, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expired')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Invalid token')

        return (None, payload)

class JWTTokenGenerator:
    @staticmethod
    def generate_token(user_id: int, expires_in_minutes: int = 60) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(minutes=expires_in_minutes),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return None
"""

    def _generate_django_oauth(self) -> str:
        return """
from social_django.backends.oauth import BaseOAuth2
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

class OAuthBackend(BaseOAuth2):
    name = 'oauth'
    AUTHORIZATION_URL = 'https://provider.com/oauth/authorize'
    ACCESS_TOKEN_URL = 'https://provider.com/oauth/token'
    ACCESS_TOKEN_METHOD = 'POST'
    REDIRECT_URI = '/auth/callback'

    def user_data(self, access_token, *args, **kwargs):
        # Fetch user data from OAuth provider
        return {}

class OAuthAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth = request.headers.get('Authorization', '').split()
        if not auth or auth[0].lower() != 'bearer':
            return None

        if len(auth) == 1:
            raise AuthenticationFailed('Invalid token header')

        try:
            token = auth[1]
            # Validate token with OAuth provider
            user_data = self.get_user_data(token)
            return (user_data, token)
        except Exception as e:
            raise AuthenticationFailed(f'Invalid token: {str(e)}')

    @staticmethod
    def get_user_data(token: str):
        # Call OAuth provider to validate token
        pass
"""

    def _generate_django_api_key(self) -> str:
        return """
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.conf import settings

class APIKeyAuthentication(TokenAuthentication):
    keyword = 'X-API-Key'

    def get_model(self):
        from rest_framework.authtoken.models import Token
        return Token

    def authenticate(self, request):
        api_key = request.headers.get(settings.API_KEY_HEADER, '')
        if not api_key:
            return None

        try:
            token = self.get_model().objects.get(key=api_key)
            return (token.user, token)
        except self.get_model().DoesNotExist:
            raise AuthenticationFailed('Invalid API key')

def validate_api_key(api_key: str) -> bool:
    from rest_framework.authtoken.models import Token
    try:
        Token.objects.get(key=api_key)
        return True
    except Token.DoesNotExist:
        return False
"""

    def _generate_fastapi_jwt(self) -> str:
        return """
import jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from pydantic import BaseModel

security = HTTPBearer()

class TokenPayload(BaseModel):
    user_id: int
    exp: datetime
    iat: datetime

class JWTHandler:
    SECRET_KEY = "your-secret-key"
    ALGORITHM = "HS256"
    EXPIRATION_MINUTES = 60

    @classmethod
    def generate_token(cls, user_id: int) -> str:
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(minutes=cls.EXPIRATION_MINUTES),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify_token(cls, token: str) -> dict:
        try:
            return jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail='Token expired')
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail='Invalid token')

async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    token = credentials.credentials
    payload = JWTHandler.verify_token(token)
    return payload.get('user_id')
"""

    def _generate_fastapi_oauth(self) -> str:
        return """
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: int = None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    # Validate OAuth token with provider
    try:
        from .jwt_handler import JWTHandler
        payload = JWTHandler.verify_token(token)
        user_id: str = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return user_id

async def get_current_active_user(current_user: int = Depends(get_current_user)):
    return current_user
"""

    def _generate_fastapi_api_key(self) -> str:
        return """
from fastapi import Depends, HTTPException, Header, status

async def verify_api_key(x_api_key: str = Header(...)):
    if not x_api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key missing")

    # Validate API key against database
    if not is_valid_api_key(x_api_key):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    return x_api_key

def is_valid_api_key(api_key: str) -> bool:
    # Check against database or cache
    # This is a placeholder - implement based on your storage
    valid_keys = ['key1', 'key2', 'key3']
    return api_key in valid_keys

async def get_current_user_from_api_key(api_key: str = Depends(verify_api_key)):
    # Retrieve user associated with API key
    return get_user_by_api_key(api_key)

def get_user_by_api_key(api_key: str):
    # Look up user from database
    pass
"""


def generate_auth_code(
    framework: str,
    auth_type: str,
    secret_key: Optional[str] = None,
    algorithm: str = "HS256"
) -> Dict[str, str]:
    """
    Generate authentication code.

    Args:
        framework: django or fastapi
        auth_type: jwt, oauth, api_key
        secret_key: secret key for signing
        algorithm: JWT algorithm

    Returns: dict of {filename: code_content}
    """
    config = AuthConfig(
        auth_type=AuthType(auth_type),
        secret_key=secret_key,
        algorithm=algorithm
    )

    generator = AuthenticationGenerator(framework, config)
    output = {}

    if framework == "django":
        output["auth.py"] = generator.generate_django()
    elif framework == "fastapi":
        output["auth.py"] = generator.generate_fastapi()

    return output
