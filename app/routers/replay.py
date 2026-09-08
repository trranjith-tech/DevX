from typing import Any

from fastapi import APIRouter, Depends

from app.schemas import ApiResponse, ReplayAction, ReplayResponse
from app.security import get_current_user
from app.services.replay_service import replay_service

router = APIRouter(prefix="/api/replay", tags=["Replay"])


@router.get("/{session_id}", response_model=ApiResponse[ReplayResponse])
def get_replay(
    session_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[ReplayResponse]:
    interactions = replay_service.get_replay(session_id, current_user["id"])
    actions = [ReplayAction.model_validate(i) for i in interactions]
    return ApiResponse(
        message="Replay retrieved",
        data=ReplayResponse(session_id=session_id, total_actions=len(actions), actions=actions),
    )
