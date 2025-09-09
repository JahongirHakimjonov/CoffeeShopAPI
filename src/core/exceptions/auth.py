from fastapi import status

from core.exceptions.base import APIException


class InvalidCredentialsError(APIException):
    """Raised when credentials are invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "invalid_credentials"
    default_detail = "Invalid email or password"


class InvalidTokenError(APIException):
    """Raised when token is invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "invalid_token"
    default_detail = "Invalid token"


class InvalidRefreshTokenError(APIException):
    """Raised when refresh token is invalid."""

    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "invalid_refresh_token"
    default_detail = "Invalid refresh token"
