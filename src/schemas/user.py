from datetime import datetime

from pydantic import EmailStr, Field, model_validator

from schemas.base import BaseSchema


class UserRegisterSchema(BaseSchema):
    email: EmailStr = Field(description="User email address", examples=["user@example.com"])
    first_name: str | None = Field(None, max_length=100, description="User's first name")
    last_name: str | None = Field(None, max_length=100, description="User's last name")
    password: str = Field(..., min_length=6, max_length=128, description="User password")
    password_confirm: str = Field(..., min_length=6, max_length=128, description="Password confirmation")

    @model_validator(mode="after")
    def check_passwords(self) -> "UserRegisterSchema":
        if self.password != self.password_confirm:
            raise ValueError("Passwords do not match")
        return self


class UserReadSchema(BaseSchema):
    id: int = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    first_name: str | None = Field(None, description="User's first name")
    last_name: str | None = Field(None, description="User's last name")
    is_verified: bool = Field(..., description="User's email verification status")
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")


class UserUpdateSchema(BaseSchema):
    first_name: str | None = Field(None, description="User's first name")
    last_name: str | None = Field(None, description="User's last name")
