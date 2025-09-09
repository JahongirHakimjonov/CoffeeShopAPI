from pydantic import EmailStr, Field

from schemas.base import BaseSchema


class ConfirmSchema(BaseSchema):
    email: EmailStr = Field(..., description="User email address")
    code: int = Field(..., description="Confirmation code")


class ConfirmResendSchema(BaseSchema):
    email: EmailStr = Field(..., description="User email address")
