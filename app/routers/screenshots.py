from typing import Any

from fastapi import APIRouter, Depends, status

from app.schemas import ApiResponse, ScreenshotCreate, ScreenshotResponse
from app.security import get_current_user
from app.services.screenshot_service import screenshot_service

router = APIRouter(prefix="/api/screenshots", tags=["Screenshot Metadata"])


@router.post("", response_model=ApiResponse[ScreenshotResponse], status_code=status.HTTP_201_CREATED)
def create_screenshot(
    payload: ScreenshotCreate, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[ScreenshotResponse]:
    screenshot = screenshot_service.create(payload, current_user["id"])
    return ApiResponse(message="Screenshot metadata recorded", data=ScreenshotResponse.model_validate(screenshot))


@router.get("/session/{session_id}", response_model=ApiResponse[list[ScreenshotResponse]])
def list_screenshots(
    session_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[list[ScreenshotResponse]]:
    screenshots = screenshot_service.list_for_session(session_id, current_user["id"])
    return ApiResponse(
        message="Screenshots retrieved",
        data=[ScreenshotResponse.model_validate(s) for s in screenshots],
    )
