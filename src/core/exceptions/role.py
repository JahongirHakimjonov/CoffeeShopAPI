from fastapi import status

from core.exceptions.base import APIException


class PermissionDeniedError(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "permission_denied"
    default_detail = "Permission denied"


class UnauthorizedError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_code = "unauthorized"
    default_detail = "Unauthorized"
