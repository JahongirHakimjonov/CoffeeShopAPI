from fastapi import status

from core.exceptions.base import APIException


class ConfirmError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "confirm_error"
    default_detail = "Confirmation error"
