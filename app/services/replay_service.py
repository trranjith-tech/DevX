from typing import Any

from app.services.session_service import session_service
from app.store import store


class ReplayService:
    def get_replay(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        session_service.get_by_session_id(session_id, user_id)
        interactions = store.interactions.find_all(lambda i: i["session_id"] == session_id)
        return sorted(interactions, key=lambda i: (i["sequence_number"], i["timestamp"]))


replay_service = ReplayService()
