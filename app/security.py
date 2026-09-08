from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings
from app.exceptions import InactiveUserException, InvalidCredentialsException
from app.store import store

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(subject: str) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    payload = {"sub": subject, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError:
        raise InvalidCredentialsException("Invalid or expired token", "INVALID_TOKEN")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    if credentials is None:
        raise InvalidCredentialsException("Missing bearer token", "MISSING_TOKEN")

    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    user = store.users.get(user_id) if user_id else None
    if user is None:
        raise InvalidCredentialsException("User for token not found", "INVALID_TOKEN")
    if not user.get("is_active", True):
        raise InactiveUserException("User account is inactive", "INACTIVE_USER")
    return user
