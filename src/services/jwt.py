import hashlib
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

import jwt
from fastapi import Depends
from passlib.context import CryptContext

from core.exceptions.auth import (
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from core.exceptions.user import UserNotFound
from core.settings import jwt_settings
from db.crud.user import UserCRUD, get_user_crud
from schemas.auth import RefreshTokenSchema, TokenPayload, TokenSchema


class JWTAuthentication:
    def __init__(
        self,
        algorithm: str = "HS256",
        access_key: str | None = None,  # secret for HS256 or private key for RS256
        refresh_key: str | None = None,  # secret for HS256 or private key for RS256
        access_token_expire_seconds: int = 1800,  # 30 min
        refresh_token_expire_seconds: int = 604800,  # 7 days
    ):
        self.algorithm = algorithm
        self.access_key = access_key
        self.refresh_key = refresh_key

        self.access_token_expire = timedelta(seconds=access_token_expire_seconds)
        self.refresh_token_expire = timedelta(seconds=refresh_token_expire_seconds)
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    @staticmethod
    async def _build_payload(user_id: int, expires_delta: timedelta) -> dict[str, Any]:
        now = datetime.now(UTC)
        exp = now + expires_delta
        iat = int(now.timestamp())
        raw = f"{user_id}-{iat}".encode()
        jti = hashlib.sha256(raw).hexdigest()

        return {
            "sub_id": user_id,
            "iat": iat,
            "exp": int(exp.timestamp()),
            "jti": jti,
        }

    async def _create_access_token(self, user_id: int) -> str:
        payload = await self._build_payload(user_id, self.access_token_expire)
        return jwt.encode(payload, self.access_key, algorithm=self.algorithm)

    async def _create_refresh_token(self, user_id: int) -> str:
        payload = await self._build_payload(user_id, self.refresh_token_expire)
        return jwt.encode(payload, self.refresh_key, algorithm=self.algorithm)

    async def authenticate(
        self, credentials: dict, user_crud: Annotated[UserCRUD, Depends(get_user_crud)]
    ) -> TokenSchema:
        try:
            user = await user_crud.get_by_email(credentials["email"])
        except UserNotFound:
            raise InvalidCredentialsError from None
        if not user or not await self._verify_password(credentials["password"], user.password):
            raise InvalidCredentialsError
        if not user.is_verified:
            raise InvalidCredentialsError

        return TokenSchema(
            access_token=await self._create_access_token(user.id),
            refresh_token=await self._create_refresh_token(user.id),
            token_type="bearer",  # noqa: S106
        )

    async def refresh_token(
        self, refresh_token: str, user_crud: Annotated[UserCRUD, Depends(get_user_crud)]
    ) -> RefreshTokenSchema:
        try:
            verify_key = self.refresh_key
            payload = jwt.decode(refresh_token, verify_key, algorithms=[self.algorithm])
            token_data = TokenPayload.model_validate(payload)

            user = await user_crud.get_by_id(token_data.sub_id)
            if not user:
                raise InvalidRefreshTokenError

            return RefreshTokenSchema(access_token=await self._create_access_token(user.id))
        except jwt.PyJWTError as err:
            raise InvalidRefreshTokenError from err

    async def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)


auth_strategy = JWTAuthentication(
    algorithm=jwt_settings.algorithm,
    access_key=jwt_settings.secret_key,
    refresh_key=jwt_settings.secret_key,
    access_token_expire_seconds=jwt_settings.access_token_expire,
    refresh_token_expire_seconds=jwt_settings.ref_token_expire,
)
