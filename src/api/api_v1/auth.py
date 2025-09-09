from typing import Annotated

from fastapi import APIRouter, Depends, status

from db.crud.user import UserCRUD, get_user_crud
from db.models.user import User
from schemas.auth import (
    AuthSchema,
    RefreshRequestSchema,
    RefreshTokenSchema,
    TokenSchema,
)
from schemas.confirm import ConfirmResendSchema, ConfirmSchema
from schemas.user import UserReadSchema, UserRegisterSchema
from services.jwt import auth_strategy

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/login",
    summary="User login",
    description="Authenticate a user with email and password and return access/refresh tokens.",
)
async def login(obj_in: AuthSchema, user_crud: Annotated[UserCRUD, Depends(get_user_crud)]) -> TokenSchema:
    return await auth_strategy.authenticate(obj_in.model_dump(), user_crud)


@router.post(
    "/refresh",
    summary="Refresh access token",
    description="Generate a new access token using a valid refresh token.",
)
async def refresh(
    refresh_token: RefreshRequestSchema,
    user_crud: Annotated[UserCRUD, Depends(get_user_crud)],
) -> RefreshTokenSchema:
    return await auth_strategy.refresh_token(refresh_token.refresh_token, user_crud)


@router.post(
    "/signup",
    response_model=UserReadSchema,
    status_code=status.HTTP_201_CREATED,
    summary="User registration",
    description="Register a new user in the system.",
)
async def signup(crud: Annotated[UserCRUD, Depends(get_user_crud)], payload: UserRegisterSchema) -> User:
    """Register a new user in the system."""
    return await crud.registration(data=payload)


@router.post(
    "/verify",
    response_model=None,
    status_code=status.HTTP_200_OK,
    summary="Confirm email",
    description="Confirm a user's email using the provided verification code.",
)
async def confirm(
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    payload: ConfirmSchema,
) -> dict:
    """Confirm a user's email using the provided verification code."""
    is_confirmed = await crud.confirm(email=payload.email, code=payload.code)
    if not is_confirmed:
        return {"detail": "Invalid confirmation code or email"}
    return {"detail": "Email confirmed successfully"}


@router.post(
    "/resend",
    status_code=status.HTTP_200_OK,
    summary="Resend confirmation code",
    description="Resend the email confirmation code to the user's email address.",
)
async def resend_confirmation(
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    payload: ConfirmResendSchema,
) -> ConfirmResendSchema:
    """Resend the email confirmation code to the user's email address."""
    await crud.resend_confirmation(email=payload.email)
    return payload
