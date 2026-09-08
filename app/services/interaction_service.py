from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas import InteractionCreate
from app.services.session_service import session_service
from app.store import store


class InteractionService:
    def create(self, payload: InteractionCreate, user_id: str) -> dict[str, Any]:
        session_service.get_by_session_id(payload.session_id, user_id)

        sequence_number = payload.sequence_number
        if sequence_number is None:
            existing = store.interactions.find_all(lambda i: i["session_id"] == payload.session_id)
            sequence_number = (max((i["sequence_number"] for i in existing), default=0)) + 1

        interaction = {
            "id": str(uuid4()),
            "session_id": payload.session_id,
            "action_type": payload.action_type,
            "timestamp": payload.timestamp or datetime.now(timezone.utc),
            "screen_name": payload.screen_name,
            "action_data": payload.action_data,
            "sequence_number": sequence_number,
        }
        store.interactions.create(interaction)
        return interaction

    def list_for_session(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        session_service.get_by_session_id(session_id, user_id)
        interactions = store.interactions.find_all(lambda i: i["session_id"] == session_id)
        return sorted(interactions, key=lambda i: (i["sequence_number"], i["timestamp"]))


interaction_service = InteractionService()
