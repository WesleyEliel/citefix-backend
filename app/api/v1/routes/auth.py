import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm

from app.api.v1.routes.utils import response_helper
from app.api.v1.services.auth import AuthService, get_auth_service
from app.api.v1.services.email import EmailService, get_email_service
from app.core.configs import settings
from app.core.security import create_access_token, verify_password
from app.db.managers.users import UserManager, get_user_manager
from app.db.models.auth import PasswordResetRequest, PasswordResetConfirm, EmailVerificationRequest, Token, \
    RefreshTokenRequest, TokenRequest
from app.db.models.users import UserPublic, UserCreate

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", response_model=UserPublic)
async def register(
        user_create: UserCreate,
        background_tasks: BackgroundTasks,
        auth_service: AuthService = Depends(get_auth_service),
        email_service: EmailService = Depends(get_email_service),
        user_manager: UserManager = Depends(get_user_manager)
):
    existing_user = await user_manager.get_by_email(user_create.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = await user_manager.create_user(user_create)
    # Send verification email
    verification_token = auth_service.create_email_verification_token(user.email)
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

    # email_service.send_email_background(
    #     background_tasks,
    #     "Verify your email",
    #     [user.email],
    #     "verify_email.html",
    #     {"verification_url": verification_url, "user": user}
    # )
    return response_helper(user)


@router.post("/token", response_model=Token)
async def login_for_access_token(
        form_data: TokenRequest,
        auth_service: AuthService = Depends(get_auth_service)
):
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    return await auth_service.create_tokens(user.email)


@router.post("/token/refresh", response_model=Token)
async def refresh_access_token(
        request: RefreshTokenRequest,
        auth_service: AuthService = Depends(get_auth_service),
        user_manager=Depends(get_user_manager)
):
    username = auth_service.verify_refresh_token(request.refresh_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_manager.get_by_email(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return await auth_service.create_tokens(user.email)


@router.post("/password-reset/request")
async def request_password_reset(
        request: PasswordResetRequest,
        background_tasks: BackgroundTasks,
        auth_service: AuthService = Depends(get_auth_service),
        email_service: EmailService = Depends(get_email_service),
        user_manager=Depends(get_user_manager)
):
    user = await user_manager.get_by_email(request.email)
    if user:
        reset_token = auth_service.create_password_reset_token(user.email)
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

        email_service.send_email_background(
            background_tasks,
            "Password Reset Request",
            [user.email],
            "password_reset.html",
            {"reset_url": reset_url, "user": user}
        )

    # Always return success to prevent email enumeration
    return {"message": "If the email exists, a password reset link has been sent"}


@router.post("/password-reset/confirm")
async def confirm_password_reset(
        request: PasswordResetConfirm,
        auth_service: AuthService = Depends(get_auth_service),
        user_manager=Depends(get_user_manager)
):
    email = auth_service.verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    user = await user_manager.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    hashed_password = auth_service.get_password_hash(request.new_password)
    await user_manager.update(user.id, {"hashed_password": hashed_password})

    return {"message": "Password updated successfully"}


@router.post("/verify-email")
async def verify_email(
        request: EmailVerificationRequest,
        auth_service: AuthService = Depends(get_auth_service),
        user_manager=Depends(get_user_manager)
):
    email = auth_service.verify_email_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    user = await user_manager.get_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if user.is_verified:
        return {"message": "Email already verified"}

    await user_manager.update(user.id, {"is_verified": True})

    return {"message": "Email verified successfully"}


@router.post("/token")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends(),
        manager: UserManager = Depends(get_user_manager)
):
    user = await manager.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=400,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
