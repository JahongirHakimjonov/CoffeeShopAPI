from collections.abc import Awaitable, Callable, Iterable
from typing import Annotated

from fastapi import Depends, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from core.auth.jwt_auth import JWTHandler
from core.constants.role import UserRole
from core.exceptions.role import PermissionDeniedError, UnauthorizedError
from core.exceptions.user import UserNotFound
from core.settings import jwt_settings
from db.crud.user import UserCRUD, get_user_crud
from schemas.auth import TokenPayload

security = HTTPBearer()
jwt_handler = JWTHandler(
    secret_key=jwt_settings.secret_key,
    algorithm=jwt_settings.algorithm,
)


def get_current_user(
    roles: Iterable[UserRole] | None = None,
) -> Callable[..., Awaitable[TokenPayload]]:
    """
    Dependency factory. Use as:
      Depends(get_current_user(roles=[UserRole.ADMIN]))
    or use the default dependency (any authenticated user):
      Depends(get_current_user())
    """

    async def _dependency(
        credentials: Annotated[HTTPAuthorizationCredentials, Security(security)],
        user_crud: UserCRUD = Depends(get_user_crud),
    ) -> TokenPayload:
        # 1) check scheme
        if credentials.scheme.lower() != "bearer":
            raise PermissionDeniedError()

        # 2) verify token (returns TokenPayload)
        try:
            token_payload: TokenPayload = jwt_handler.verify_token(credentials.credentials)
        except Exception as exc:
            logger.error(f"JWT verification failed: {exc}")
            raise UnauthorizedError() from exc

        # 3) validate subject
        if not isinstance(token_payload.sub_id, int):
            logger.error("Invalid token: sub must be int or str")
            raise UnauthorizedError()

        # 4) get user from DB
        user_id = token_payload.sub_id
        try:
            user = await user_crud.get_by_id(user_id)
        except UserNotFound:
            logger.error(f"User not found for sub={user_id}")
            raise UnauthorizedError() from None

        # 5) check role(s) if provided
        if roles:
            allowed = {r if isinstance(r, UserRole) else UserRole(r) for r in roles}
            user_role = getattr(user, "role", None)
            if user_role is None or user_role not in allowed:
                raise PermissionDeniedError()

        return token_payload

    return _dependency


# default dependency
current_user_dependency = get_current_user()
