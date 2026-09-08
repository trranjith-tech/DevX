from typing import Any

from fastapi import APIRouter, Depends, status

from app.schemas import ApiResponse, MetricCreate, MetricResponse
from app.security import get_current_user
from app.services.metric_service import metric_service

router = APIRouter(prefix="/api/metrics", tags=["Performance Metrics"])


@router.post("", response_model=ApiResponse[MetricResponse], status_code=status.HTTP_201_CREATED)
def create_metric(
    payload: MetricCreate, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[MetricResponse]:
    metric = metric_service.create(payload, current_user["id"])
    return ApiResponse(message="Metric recorded", data=MetricResponse.model_validate(metric))


@router.get("/session/{session_id}", response_model=ApiResponse[list[MetricResponse]])
def list_metrics(
    session_id: str, current_user: dict[str, Any] = Depends(get_current_user)
) -> ApiResponse[list[MetricResponse]]:
    metrics = metric_service.list_for_session(session_id, current_user["id"])
    return ApiResponse(
        message="Metrics retrieved", data=[MetricResponse.model_validate(m) for m in metrics]
    )
