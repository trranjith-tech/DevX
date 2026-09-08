from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.enums import InteractionType, IssueType, SessionStatus, Severity

T = TypeVar("T")


# ---------- Common envelope ----------

class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    message: str = "Operation successful"
    data: Optional[T] = None


# ---------- Auth ----------

class UserRegister(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: EmailStr
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- Session ----------

class SessionStartRequest(BaseModel):
    app_name: str = Field(min_length=1, max_length=200)
    device_model: str = Field(min_length=1, max_length=120)
    android_version: str = Field(min_length=1, max_length=30)


class SessionEndRequest(BaseModel):
    session_id: str
    status: SessionStatus = SessionStatus.COMPLETED

    @field_validator("status")
    @classmethod
    def must_be_terminal(cls, value: SessionStatus) -> SessionStatus:
        if value == SessionStatus.STARTED:
            raise ValueError("status must be a terminal state (COMPLETED, FAILED, CANCELLED)")
        return value


class SessionResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    app_name: str
    device_model: str
    android_version: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: SessionStatus
    created_at: datetime


# ---------- Metrics ----------

class MetricCreate(BaseModel):
    session_id: str
    fps: float = Field(ge=0)
    memory_usage: float = Field(ge=0)
    battery_usage: float = Field(ge=0)
    cpu_usage: float = Field(ge=0, le=100)
    temperature: float = Field(ge=-20, le=150)
    frame_drops: int = Field(ge=0)
    recorded_at: Optional[datetime] = None


class MetricResponse(BaseModel):
    id: str
    session_id: str
    fps: float
    memory_usage: float
    battery_usage: float
    cpu_usage: float
    temperature: float
    frame_drops: int
    recorded_at: datetime


# ---------- Interactions ----------

class InteractionCreate(BaseModel):
    session_id: str
    action_type: InteractionType
    timestamp: Optional[datetime] = None
    screen_name: str = Field(min_length=1, max_length=200)
    action_data: dict[str, Any] = Field(default_factory=dict)
    sequence_number: Optional[int] = None


class InteractionResponse(BaseModel):
    id: str
    session_id: str
    action_type: InteractionType
    timestamp: datetime
    screen_name: str
    action_data: dict[str, Any]
    sequence_number: int


# ---------- Screenshots ----------

class ScreenshotCreate(BaseModel):
    session_id: str
    timestamp: Optional[datetime] = None
    screen_name: str = Field(min_length=1, max_length=200)
    file_name: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=500)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScreenshotResponse(BaseModel):
    id: str
    session_id: str
    timestamp: datetime
    screen_name: str
    file_name: str
    storage_path: str
    width: int
    height: int
    metadata: dict[str, Any]


# ---------- AI ----------

class AIAnalyzeRequest(BaseModel):
    session_id: str


class AIReportItem(BaseModel):
    issue_type: IssueType
    severity: Severity
    root_cause: str
    explanation: str
    suggested_fix: str
    confidence_score: float = Field(ge=0, le=1)


class AIReportResponse(BaseModel):
    id: str
    session_id: str
    issue_type: IssueType
    severity: Severity
    root_cause: str
    explanation: str
    suggested_fix: str
    confidence_score: float
    created_at: datetime


class AIAnalyzeResponse(BaseModel):
    session_id: str
    reports: list[AIReportResponse]


# ---------- Replay ----------

class ReplayAction(BaseModel):
    sequence_number: int
    action_type: InteractionType
    timestamp: datetime
    screen_name: str
    action_data: dict[str, Any]


class ReplayResponse(BaseModel):
    session_id: str
    total_actions: int
    actions: list[ReplayAction]
