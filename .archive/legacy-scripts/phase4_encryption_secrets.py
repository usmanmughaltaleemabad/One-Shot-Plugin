#!/usr/bin/env python3
"""
Phase 4 Security: Encryption and Secrets Management

Encrypt sensitive data and manage secrets securely.

Encryption requirements:
- At rest: stored data encrypted
- In transit: transmitted data encrypted
- Keys: secure key management, rotation
- No hardcoded secrets: use vault/environment

Secrets to protect:
- Database passwords
- API keys
- Private keys
- Session tokens
- Customer data

Usage:
    python phase4_encryption_secrets.py --secret-type api-key

Input: Secret type
Output: Encryption and secrets management patterns
"""

import argparse
import json
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timedelta


def generate_encryption_manager() -> str:
    """Generate encryption manager."""

    encryption = '''
class EncryptionManager:
    """
    Encrypt/decrypt sensitive data.

    Methods:
    - AES-256 for data at rest
    - TLS/SSL for data in transit
    - Key rotation every 90 days
    """

    def __init__(self, key: str):
        self.key = key
        self.algorithm = "AES-256"

    def encrypt(self, plaintext: str) -> str:
        """Encrypt sensitive data"""
        # In production: use cryptography library
        # from cryptography.fernet import Fernet
        # cipher = Fernet(key)
        # ciphertext = cipher.encrypt(plaintext.encode())

        # Simplified for example:
        return f"encrypted:{plaintext}"

    def decrypt(self, ciphertext: str) -> str:
        """Decrypt sensitive data"""
        # In production: use cryptography library
        return ciphertext.replace("encrypted:", "")

    def encrypt_field(self, obj: Dict, field: str) -> Dict:
        """Encrypt specific field in object"""
        result = obj.copy()
        if field in result:
            result[field] = self.encrypt(str(result[field]))
        return result

    def decrypt_field(self, obj: Dict, field: str) -> Dict:
        """Decrypt specific field in object"""
        result = obj.copy()
        if field in result:
            result[field] = self.decrypt(result[field])
        return result

    def rotate_key(self, new_key: str) -> None:
        """Rotate encryption key"""
        self.key = new_key
        self.key_rotation_date = datetime.utcnow()
'''

    return encryption


def generate_secrets_vault() -> str:
    """Generate secrets vault."""

    vault = '''
class SecretsVault:
    """
    Secure storage for secrets (passwords, API keys, etc).

    Never:
    - Hardcode secrets in code
    - Store in version control
    - Log secrets
    - Transmit unencrypted

    Always:
    - Use vault/environment variables
    - Rotate regularly
    - Audit access
    - Use strong generation
    """

    def __init__(self):
        self._secrets = {}  # name → encrypted_value
        self._access_log = []

    def store_secret(self, name: str, value: str, ttl_days: int = 365) -> None:
        """Store secret securely"""
        self._secrets[name] = {
            "value": value,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(days=ttl_days)).isoformat()
        }

    def retrieve_secret(self, name: str, accessor: str) -> Optional[str]:
        """Retrieve secret (with audit log)"""
        if name not in self._secrets:
            return None

        secret = self._secrets[name]

        # Check expiration
        expires_at = datetime.fromisoformat(secret["expires_at"])
        if datetime.utcnow() > expires_at:
            return None  # Expired

        # Log access
        self._access_log.append({
            "secret": name,
            "accessor": accessor,
            "timestamp": datetime.utcnow().isoformat()
        })

        return secret["value"]

    def rotate_secret(self, name: str, new_value: str) -> None:
        """Rotate secret to new value"""
        if name in self._secrets:
            self._secrets[name]["rotated_at"] = datetime.utcnow().isoformat()
            self._secrets[name]["value"] = new_value

    def get_access_log(self) -> List[Dict]:
        """Get audit log of secret access"""
        return self._access_log.copy()

    def get_expiring_secrets(self, days_until: int = 30) -> List[str]:
        """Get secrets expiring soon"""
        expiring = []
        threshold = datetime.utcnow() + timedelta(days=days_until)

        for name, secret in self._secrets.items():
            expires_at = datetime.fromisoformat(secret["expires_at"])
            if expires_at < threshold:
                expiring.append(name)

        return expiring
'''

    return vault


def generate_key_management() -> str:
    """Generate key management."""

    keys = '''
class KeyManagementService:
    """
    Manage encryption keys.

    Requirements:
    - Secure generation
    - Secure storage
    - Regular rotation
    - Audit tracking
    - Backup/recovery
    """

    def __init__(self):
        self._keys = {}  # key_id → {key, created_at, rotated_at}
        self._rotation_schedule = {}  # key_id → 90_days

    def generate_key(self, key_id: str, length: int = 256) -> str:
        """Generate new encryption key"""
        import secrets
        key = secrets.token_hex(length // 8)

        self._keys[key_id] = {
            "key": key,
            "created_at": datetime.utcnow().isoformat(),
            "rotated_at": None,
            "version": 1,
            "active": True
        }

        return key

    def get_active_key(self, key_id: str) -> Optional[str]:
        """Get currently active key"""
        if key_id not in self._keys:
            return None

        key_data = self._keys[key_id]
        if key_data["active"]:
            return key_data["key"]

        return None

    def rotate_key(self, key_id: str) -> str:
        """Rotate key to new version"""
        if key_id not in self._keys:
            return None

        # Mark old key as inactive
        self._keys[key_id]["active"] = False

        # Generate new key
        new_key = self.generate_key(f"{key_id}_v{len(self._keys)}")
        self._keys[key_id] = {
            "key": new_key,
            "created_at": datetime.utcnow().isoformat(),
            "rotated_at": datetime.utcnow().isoformat(),
            "version": self._keys[key_id].get("version", 1) + 1,
            "active": True
        }

        return new_key

    def schedule_rotation(self, key_id: str, days: int = 90) -> None:
        """Schedule automatic key rotation"""
        self._rotation_schedule[key_id] = days

    def get_keys_needing_rotation(self) -> List[str]:
        """Get keys that need rotation"""
        needing_rotation = []

        for key_id, schedule_days in self._rotation_schedule.items():
            if key_id not in self._keys:
                continue

            key_data = self._keys[key_id]
            rotated_at = datetime.fromisoformat(key_data.get("rotated_at", key_data["created_at"]))

            if (datetime.utcnow() - rotated_at).days > schedule_days:
                needing_rotation.append(key_id)

        return needing_rotation
'''

    return keys


def generate_encryption_system() -> dict:
    """Generate complete encryption system."""

    imports = '''import secrets
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta


'''

    module_doc = '''"""
Phase 4 Security: Encryption & Secrets Management

Protect sensitive data with encryption and secrets.

Threats:
1. Data at rest: database hacked, data exposed
2. Data in transit: network intercepted, data exposed
3. Secrets exposed: hardcoded API keys, version control exposed
4. Key compromise: encryption key stolen, all data compromised

Mitigations:

1. Encryption at Rest
   - Customer data encrypted with AES-256
   - Stored in encrypted database
   - Decrypted only when needed
   - Cannot read without key

2. Encryption in Transit
   - TLS 1.3 for all network traffic
   - Certificate pinning for critical paths
   - Perfect forward secrecy

3. Secrets Management
   - Database passwords in vault (not code)
   - API keys in environment variables
   - Rotation every 90 days
   - Audit log of all access

4. Key Management
   - Keys generated securely (cryptographic randomness)
   - Keys stored separately from data
   - Regular rotation (every 90 days)
   - Backup for recovery
   - Audit trail of key access

Example: Password Storage

Bad:
- Store plaintext password in database (WRONG!)
- When hacked: all passwords exposed

Good:
- Hash password with salt (bcrypt)
- Store hash in database
- When hacked: hashes useless without salt

Better:
- Encrypt password with AES-256
- Store encrypted password in database
- Separately store encryption key in vault
- When hacked: encrypted passwords useless without key

Best:
- Hash password (bcrypt)
- Also encrypt hash
- Store encrypted hash
- Key in separate vault with rotation
- Multi-layer protection

Timeline:
- User creates account → generate random salt, bcrypt password
- Password stored encrypted → key in vault
- Every 90 days → rotate encryption key (old passwords re-encrypted with new key)
- User logs in → decrypt password, compare hash
- Secret accessed → log who accessed what when
"""
'''

    encryption = generate_encryption_manager()
    vault = generate_secrets_vault()
    keys = generate_key_management()

    complete_code = imports + module_doc + "\n" + encryption + "\n" + vault + "\n" + keys

    return {
        "code": complete_code,
        "pattern": "Encryption and Secrets Management",
        "module": "phase4_encryption_secrets.py",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate encryption and secrets management")
    parser.add_argument("--secret-type", help="Type of secret")
    parser.add_argument("--output", choices=["json", "code"], default="code")

    args = parser.parse_args()
    result = generate_encryption_system()

    if args.output == "json":
        metadata = {k: v for k, v in result.items() if k != "code"}
        print(json.dumps(metadata, indent=2))
    else:
        print(result["code"])


if __name__ == "__main__":
    main()
