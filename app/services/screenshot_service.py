from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas import ScreenshotCreate
from app.services.session_service import session_service
from app.store import store


class ScreenshotService:
    def create(self, payload: ScreenshotCreate, user_id: str) -> dict[str, Any]:
        session_service.get_by_session_id(payload.session_id, user_id)

        screenshot = {
            "id": str(uuid4()),
            "session_id": payload.session_id,
            "timestamp": payload.timestamp or datetime.now(timezone.utc),
            "screen_name": payload.screen_name,
            "file_name": payload.file_name,
            "storage_path": payload.storage_path,
            "width": payload.width,
            "height": payload.height,
            "metadata": payload.metadata,
        }
        store.screenshots.create(screenshot)
        return screenshot

    def list_for_session(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        session_service.get_by_session_id(session_id, user_id)
        screenshots = store.screenshots.find_all(lambda s: s["session_id"] == session_id)
        return sorted(screenshots, key=lambda s: s["timestamp"])


screenshot_service = ScreenshotService()
