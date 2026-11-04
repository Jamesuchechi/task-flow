from datetime import datetime, timedelta, UTC
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

from app.core.config import get_settings

settings = get_settings()

password_hash = PasswordHash([Argon2Hasher()])

def hash_password(raw: str) -> str:
    return password_hash.hash(raw)

def verify_password(raw: str, hashed: str) -> bool:
    return password_hash.verify(raw, hashed)

def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(UTC)

    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": now,
        "exp": now + timedelta(minutes=settings.access_token_minutes)
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token has expired")
    except jwt.InvalidTokenError:
        raise ValueError("Invalid token")
