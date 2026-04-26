import base64
import hashlib

from cryptography.fernet import Fernet

from config import settings


def _build_fernet() -> Fernet:
    digest = hashlib.sha256(settings.session_secret_key.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


fernet = _build_fernet()


def encrypt_session(value: str) -> str:
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_session(value: str) -> str:
    return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
