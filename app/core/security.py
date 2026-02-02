import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import settings


def _load_encryption_key() -> bytes:
    if not settings.encryption_key_b64:
        raise ValueError("ENCRYPTION_KEY_B64 is required")
    key = base64.b64decode(settings.encryption_key_b64)
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY_B64 must be 32 bytes for AES-256")
    return key


def encrypt_secret(plaintext: str) -> str:
    key = _load_encryption_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    payload = nonce + ciphertext
    return base64.b64encode(payload).decode("utf-8")


def decrypt_secret(ciphertext_b64: str) -> str:
    key = _load_encryption_key()
    payload = base64.b64decode(ciphertext_b64)
    nonce = payload[:12]
    ciphertext = payload[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_minutes)
    payload = {"sub": subject, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_access_token(token: str) -> str:
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    return payload["sub"]


def sign_webhook_payload(payload: bytes) -> str:
    signature = hmac.new(settings.webhook_secret.encode("utf-8"), payload, hashlib.sha256)
    return signature.hexdigest()


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    expected = sign_webhook_payload(payload)
    return hmac.compare_digest(expected, signature)
