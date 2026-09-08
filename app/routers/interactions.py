from typing import Any

from fastapi import APIRouter, Depends, status

from app.schemas import ApiResponse, InteractionCreate, InteractionResponse
from app.security import get_current_user
from app.services.interaction_service import interaction_service

router = APIRouter(prefix="/api/interactions", tags=["User Interactions"])


@router.post("", response_model=ApiResponse[InteractionResponse], status_code=status.HTTP_201_CREATED)
def create_interaction(
    payload: InteractionCreate, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[InteractionResponse]:
    interaction = interaction_service.create(payload, current_user["id"])
    return ApiResponse(message="Interaction recorded", data=InteractionResponse.model_validate(interaction))


@router.get("/session/{session_id}", response_model=ApiResponse[list[InteractionResponse]])
def list_interactions(
    session_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[list[InteractionResponse]]:
    interactions = interaction_service.list_for_session(session_id, current_user["id"])
    return ApiResponse(
        message="Interactions retrieved",
        data=[InteractionResponse.model_validate(i) for i in interactions],
    )
