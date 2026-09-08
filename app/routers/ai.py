from typing import Any

from fastapi import APIRouter, Depends

from app.schemas import AIAnalyzeRequest, AIAnalyzeResponse, AIReportResponse, ApiResponse
from app.security import get_current_user
from app.services.ai_service import ai_service

router = APIRouter(prefix="/api/ai", tags=["AI Analysis"])


@router.post("/analyze", response_model=ApiResponse[AIAnalyzeResponse])
def analyze_session(
    payload: AIAnalyzeRequest, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[AIAnalyzeResponse]:
    reports = ai_service.analyze(payload.session_id, current_user["id"])
    return ApiResponse(
        message="Analysis complete",
        data=AIAnalyzeResponse(
            session_id=payload.session_id,
            reports=[AIReportResponse.model_validate(r) for r in reports],
        ),
    )


@router.get("/report/{session_id}", response_model=ApiResponse[AIAnalyzeResponse])
def get_reports(
    session_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[AIAnalyzeResponse]:
    reports = ai_service.get_reports(session_id, current_user["id"])
    return ApiResponse(
        message="Reports retrieved",
        data=AIAnalyzeResponse(
            session_id=session_id,
            reports=[AIReportResponse.model_validate(r) for r in reports],
        ),
    )
