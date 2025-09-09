from fastapi import status

from core.exceptions.base import APIException


class UserNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "user_not_found"
    default_detail = "User not found"


class UserAlreadyRegistered(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "user_already_registered"
    default_detail = "User with this email already exists"
