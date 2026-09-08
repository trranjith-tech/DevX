from typing import Any

from fastapi import APIRouter, Depends, status

from app.schemas import ApiResponse, SessionEndRequest, SessionResponse, SessionStartRequest
from app.security import get_current_user
from app.services.session_service import session_service

router = APIRouter(prefix="/api/session", tags=["Test Sessions"])


@router.post("/start", response_model=ApiResponse[SessionResponse], status_code=status.HTTP_201_CREATED)
def start_session(
    payload: SessionStartRequest, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[SessionResponse]:
    session = session_service.start(payload, current_user["id"])
    return ApiResponse(message="Session started", data=SessionResponse.model_validate(session))


@router.put("/end", response_model=ApiResponse[SessionResponse])
def end_session(
    payload: SessionEndRequest, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[SessionResponse]:
    session = session_service.end(payload, current_user["id"])
    return ApiResponse(message="Session ended", data=SessionResponse.model_validate(session))


@router.get("/{session_id}", response_model=ApiResponse[SessionResponse])
def get_session(
    session_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[SessionResponse]:
    session = session_service.get_by_session_id(session_id, current_user["id"])
    return ApiResponse(message="Session retrieved", data=SessionResponse.model_validate(session))
