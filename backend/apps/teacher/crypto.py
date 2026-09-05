import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    raw_key = getattr(settings, "GOOGLE_TOKEN_ENCRYPTION_KEY", "")
    if raw_key:
        key = raw_key.encode()
    else:
        # Dev fallback: suy ra key hợp lệ từ SECRET_KEY để không bắt buộc cấu hình
        # thêm khi chạy local. Production nên đặt GOOGLE_TOKEN_ENCRYPTION_KEY riêng
        # (Fernet.generate_key()) vì xoay SECRET_KEY sẽ làm mất khả năng giải mã token cũ.
        digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(digest)
    return Fernet(key)


def encrypt(raw: str) -> str:
    if not raw:
        return ""
    return _fernet().encrypt(raw.encode()).decode()


def decrypt(token: str) -> str:
    if not token:
        return ""
    try:
        return _fernet().decrypt(token.encode()).decode()
    except InvalidToken:
        return ""
