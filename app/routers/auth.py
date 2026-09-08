from typing import Any

from fastapi import APIRouter, Depends, status

from app.schemas import ApiResponse, TokenResponse, UserLogin, UserRegister, UserResponse
from app.security import get_current_user
from app.services.auth_service import auth_service

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=ApiResponse[UserResponse], status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister) -> ApiResponse[UserResponse]:
    user = auth_service.register(payload)
    return ApiResponse(
        message="User registered successfully",
        data=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(payload: UserLogin) -> ApiResponse[TokenResponse]:
    token = auth_service.login(payload)
    return ApiResponse(message="Login successful", data=token)


@router.get("/profile", response_model=ApiResponse[UserResponse])
def profile(current_user: dict[str, Any] = Depends(get_current_user)) -> ApiResponse[UserResponse]:
    return ApiResponse(message="Profile retrieved", data=UserResponse.model_validate(current_user))
