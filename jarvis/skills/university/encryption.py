"""Encryption utilities for sensitive data."""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from jarvis.utils.logger import get_logger

logger = get_logger("skills.university.encryption")


class Encryptor:
    """Fernet encryption wrapper."""

    def __init__(self, master_key: str = None):
        if master_key:
            self._key = self._derive_key(master_key)
        else:
            self._key = self._get_or_create_key()
        self._fernet = Fernet(self._key)

    def _derive_key(self, password: str) -> bytes:
        """Derive key from password."""
        salt = b"jarvis_salt_v1"  # In production, store salt separately
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _get_or_create_key(self) -> bytes:
        """Get or create master key."""
        key_path = os.path.expanduser("~/.jarvis/.master_key")

        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                return f.read()

        # Create new key
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        with open(key_path, "wb") as f:
            f.write(key)
        os.chmod(key_path, 0o600)

        logger.info("Generated new master encryption key")
        return key

    def encrypt(self, data: str) -> bytes:
        """Encrypt string to bytes."""
        if not data:
            return b""
        return self._fernet.encrypt(data.encode())

    def decrypt(self, data: bytes) -> str:
        """Decrypt bytes to string."""
        if not data:
            return ""
        return self._fernet.decrypt(data).decode()


class CredentialManager:
    """Manage encrypted university credentials."""

    def __init__(self, db, encryptor: Encryptor = None):
        self.db = db
        self.encryptor = encryptor or Encryptor()

    def save_credentials(
        self,
        service: str,
        base_url: str,
        username: str,
        password: str,
    ) -> str:
        """Save credentials (encrypted)."""
        import uuid

        cred_id = str(uuid.uuid4())
        encrypted_password = self.encryptor.encrypt(password)

        self.db.execute(
            """
            INSERT INTO credentials (id, service, username, encrypted_password, base_url, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                cred_id,
                service,
                username,
                encrypted_password,
                base_url,
                datetime.utcnow().isoformat(),
            ),
        )

        logger.info(f"Saved credentials for {service}")
        return cred_id

    def get_credentials(self, service: str = "moodle") -> tuple[str, str, str]:
        """Get decrypted username and password."""
        row = self.db.query_one(
            "SELECT * FROM credentials WHERE service = ?", (service,)
        )

        if not row:
            raise ValueError(f"No credentials found for {service}")

        username = row.get("username")
        encrypted_password = row.get("encrypted_password")

        if encrypted_password:
            password = self.encryptor.decrypt(encrypted_password)
        else:
            password = None

        return username, password, row.get("base_url")

    def has_credentials(self, service: str = "moodle") -> bool:
        """Check if credentials exist."""
        row = self.db.query_one(
            "SELECT id FROM credentials WHERE service = ?", (service,)
        )
        return row is not None

    def delete_credentials(self, service: str = "moodle") -> bool:
        """Delete credentials."""
        count = self.db.delete("DELETE FROM credentials WHERE service = ?", (service,))
        return count > 0

    def update_last_sync(self, service: str = "moodle"):
        """Update last sync timestamp."""
        self.db.execute(
            "UPDATE credentials SET last_sync = ? WHERE service = ?",
            (datetime.utcnow().isoformat(), service),
        )


from datetime import datetime
