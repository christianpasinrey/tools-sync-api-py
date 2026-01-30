from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr

from src.config.settings import settings
from src.controllers import auth_controller
from src.middleware.auth import authenticate
from src.middleware.rate_limiter import (
    limiter,
    AUTH_LIMIT,
    FORGOT_PASSWORD_LIMIT,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# --- Request schemas ---


class RegisterBody(BaseModel):
    email: EmailStr
    password: str
    vaultSalt: list[int] | None = None


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordBody(BaseModel):
    currentPassword: str
    newPassword: str
    newVaultSalt: list[int]


class ForgotPasswordBody(BaseModel):
    email: EmailStr


class VerifyResetTokenBody(BaseModel):
    email: EmailStr
    token: str


class ResetAccountBody(BaseModel):
    email: EmailStr
    token: str
    newPassword: str
    newVaultSalt: list[int]


# --- Helper ---


def _set_refresh_cookie(response: Response, refresh_token: str):
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        secure=settings.is_production,
        samesite="strict" if settings.is_production else "lax",
        max_age=settings.jwt_refresh_expires_days * 24 * 60 * 60,
        path="/",
        domain=settings.cookie_domain or None,
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key="refreshToken",
        path="/",
        domain=settings.cookie_domain or None,
    )


# --- Endpoints ---


@router.post("/register")
@limiter.limit(AUTH_LIMIT)
async def register(body: RegisterBody, request: Request, response: Response):
    result = await auth_controller.register(body.email, body.password, body.vaultSalt)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}

    _set_refresh_cookie(response, result["refresh_token"])
    return result["data"]


@router.post("/login")
@limiter.limit(AUTH_LIMIT)
async def login(body: LoginBody, request: Request, response: Response):
    result = await auth_controller.login(body.email, body.password)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}

    _set_refresh_cookie(response, result["refresh_token"])
    return result["data"]


@router.post("/refresh")
@limiter.limit(AUTH_LIMIT)
async def refresh(request: Request, response: Response):
    refresh_token = request.cookies.get("refreshToken")
    if not refresh_token:
        response.status_code = 401
        return {"message": "No refresh token"}

    result = await auth_controller.refresh(refresh_token)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}

    _set_refresh_cookie(response, result["refresh_token"])
    return result["data"]


@router.post("/change-password")
async def change_password(
    body: ChangePasswordBody,
    response: Response,
    user_id: str = Depends(authenticate),
):
    result = await auth_controller.change_password(
        user_id, body.currentPassword, body.newPassword, body.newVaultSalt
    )
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}

    _clear_refresh_cookie(response)
    return result["data"]


@router.post("/logout")
async def logout(response: Response, user_id: str = Depends(authenticate)):
    result = await auth_controller.logout(user_id)
    _clear_refresh_cookie(response)
    return result["data"]


@router.post("/forgot-password")
@limiter.limit(FORGOT_PASSWORD_LIMIT)
async def forgot_password(
    body: ForgotPasswordBody, request: Request, response: Response
):
    result = await auth_controller.forgot_password(body.email)
    return result["data"]


@router.post("/verify-reset-token")
@limiter.limit(AUTH_LIMIT)
async def verify_reset_token(
    body: VerifyResetTokenBody, request: Request, response: Response
):
    result = await auth_controller.verify_reset_token(body.email, body.token)
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}
    return result["data"]


@router.post("/reset-account")
@limiter.limit(AUTH_LIMIT)
async def reset_account(
    body: ResetAccountBody, request: Request, response: Response
):
    result = await auth_controller.reset_account(
        body.email, body.token, body.newPassword, body.newVaultSalt
    )
    if "error" in result:
        response.status_code = result["status"]
        return {"message": result["error"]}

    _set_refresh_cookie(response, result["refresh_token"])
    return result["data"]
