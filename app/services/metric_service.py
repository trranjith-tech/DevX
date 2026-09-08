from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.schemas import MetricCreate
from app.services.session_service import session_service
from app.store import store


class MetricService:
    def create(self, payload: MetricCreate, user_id: str) -> dict[str, Any]:
        # Verifies the session exists and belongs to the authenticated user.
        session_service.get_by_session_id(payload.session_id, user_id)

        metric = {
            "id": str(uuid4()),
            "session_id": payload.session_id,
            "fps": payload.fps,
            "memory_usage": payload.memory_usage,
            "battery_usage": payload.battery_usage,
            "cpu_usage": payload.cpu_usage,
            "temperature": payload.temperature,
            "frame_drops": payload.frame_drops,
            "recorded_at": payload.recorded_at or datetime.now(timezone.utc),
        }
        store.metrics.create(metric)
        return metric

    def list_for_session(self, session_id: str, user_id: str) -> list[dict[str, Any]]:
        session_service.get_by_session_id(session_id, user_id)
        metrics = store.metrics.find_all(lambda m: m["session_id"] == session_id)
        return sorted(metrics, key=lambda m: m["recorded_at"])


metric_service = MetricService()
