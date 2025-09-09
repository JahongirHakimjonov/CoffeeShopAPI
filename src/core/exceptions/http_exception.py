from json import JSONDecodeError

import httpx

from core.exceptions.base import APIException


class ContactTechnicalSupportError(APIException):
    code = "something_went_wrong"
    description = "Something went wrong. Please, contact technical support"


class UserServiceError(APIException):
    def __init__(self, code: str, description: str) -> None:
        self.code = code
        self.description = description


async def raise_for_status(response: httpx.Response) -> None:
    if response.status_code in [200, 201]:
        return
    try:
        error_body = response.json()
        code = error_body["code"]
        description = error_body["description"]
        raise UserServiceError(code=code, description=description)
    except JSONDecodeError as e:
        raise ContactTechnicalSupportError() from e
