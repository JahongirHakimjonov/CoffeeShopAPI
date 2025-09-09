# core/auth/jwt_auth.py
import jwt
from fastapi import status
from loguru import logger

from core.exceptions.base import APIException
from schemas.auth import TokenPayload


class JWTHandler:
    def __init__(self, secret_key: str, algorithm: str) -> None:
        """
        JWT handler for HS256 (symmetric secret-based) tokens.
        """
        self.secret_key = secret_key
        self.algorithm = algorithm

    def verify_token(self, token: str) -> TokenPayload:
        try:
            payload = jwt.decode(str(token), self.secret_key, algorithms=[self.algorithm])
            return TokenPayload.model_validate(payload)

        except jwt.ExpiredSignatureError as e:
            logger.warning("JWT expired")
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Token expired: {e}",
            ) from e

        except jwt.InvalidTokenError as e:
            logger.error("JWT verification failed")
            logger.debug(f"Token: {token}")
            raise APIException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Invalid token: {e}",
            ) from e
