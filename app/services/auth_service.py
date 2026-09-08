from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.exceptions import InvalidCredentialsException, UserAlreadyExistsException
from app.schemas import TokenResponse, UserLogin, UserRegister
from app.security import create_access_token, hash_password, verify_password
from app.store import store


class AuthService:
    def register(self, payload: UserRegister) -> dict[str, Any]:
        existing = store.users.find_one(lambda u: u["email"].lower() == payload.email.lower())
        if existing:
            raise UserAlreadyExistsException(
                f"A user with email '{payload.email}' already exists", "USER_ALREADY_EXISTS"
            )

        now = datetime.now(timezone.utc)
        user = {
            "id": str(uuid4()),
            "name": payload.name,
            "email": payload.email,
            "password_hash": hash_password(payload.password),
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }
        store.users.create(user)
        return user

    def login(self, payload: UserLogin) -> TokenResponse:
        user = store.users.find_one(lambda u: u["email"].lower() == payload.email.lower())
        if user is None or not verify_password(payload.password, user["password_hash"]):
            raise InvalidCredentialsException("Invalid email or password", "INVALID_CREDENTIALS")
        if not user.get("is_active", True):
            raise InvalidCredentialsException("User account is inactive", "INACTIVE_USER")

        token = create_access_token(subject=user["id"])
        return TokenResponse(access_token=token)


auth_service = AuthService()
