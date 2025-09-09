from typing import Annotated

from pydantic import EmailStr, Field

from schemas.base import BaseSchema


class TokenPayload(BaseSchema):
    """Schema for JWT payload."""

    sub_id: Annotated[
        int,
        Field(description="Subject: unique user ID"),
    ]
    exp: Annotated[
        int,
        Field(description="Expiration time (Unix timestamp)"),
    ]
    iat: Annotated[
        int,
        Field(description="Issued at (Unix timestamp)"),
    ]
    jti: Annotated[
        str,
        Field(description="JWT ID: unique identifier for the token"),
    ]


class TokenSchema(BaseSchema):
    access_token: Annotated[str, Field(description="Access token")]
    refresh_token: Annotated[str, Field(description="Refresh token")]
    token_type: Annotated[str, Field(description="Type of the token, typically 'bearer'")]


class RefreshRequestSchema(BaseSchema):
    refresh_token: Annotated[str, Field(description="Refresh token used to obtain a new access token")]


class RefreshTokenSchema(BaseSchema):
    access_token: Annotated[str, Field(description="Newly issued access token")]


class AuthSchema(BaseSchema):
    email: Annotated[EmailStr, Field(description="User email address", examples=["user@example.com"])]
    password: Annotated[str, Field(description="User password")]
