from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.enums import SessionStatus
from app.exceptions import (
    SessionAlreadyCompletedException,
    SessionNotFoundException,
    UnauthorizedSessionAccessException,
)
from app.schemas import SessionEndRequest, SessionStartRequest
from app.store import store


class SessionService:
    def start(self, payload: SessionStartRequest, user_id: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc)
        session = {
            "id": str(uuid4()),
            "session_id": str(uuid4()),
            "user_id": user_id,
            "app_name": payload.app_name,
            "device_model": payload.device_model,
            "android_version": payload.android_version,
            "start_time": now,
            "end_time": None,
            "status": SessionStatus.STARTED,
            "created_at": now,
        }
        store.sessions.create(session)
        return session

    def end(self, payload: SessionEndRequest, user_id: str) -> dict[str, Any]:
        session = self._get_owned_session(payload.session_id, user_id)
        if session["status"] != SessionStatus.STARTED:
            raise SessionAlreadyCompletedException(
                f"Session '{payload.session_id}' is already {session['status']}",
                "SESSION_ALREADY_COMPLETED",
            )
        store.sessions.update(
            session["id"],
            {"status": payload.status, "end_time": datetime.now(timezone.utc)},
        )
        return store.sessions.get(session["id"])

    def get_by_session_id(self, session_id: str, user_id: str) -> dict[str, Any]:
        return self._get_owned_session(session_id, user_id)

    def _get_owned_session(self, session_id: str, user_id: str) -> dict[str, Any]:
        session = store.sessions.find_one(lambda s: s["session_id"] == session_id)
        if session is None:
            raise SessionNotFoundException(f"Session '{session_id}' not found", "SESSION_NOT_FOUND")
        if session["user_id"] != user_id:
            raise UnauthorizedSessionAccessException(
                "You do not have access to this session", "UNAUTHORIZED_SESSION_ACCESS"
            )
        return session


session_service = SessionService()
