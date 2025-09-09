from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from pydantic import TypeAdapter

from core.constants.role import UserRole
from db.crud.user import UserCRUD, get_user_crud
from db.models.user import User
from schemas.auth import TokenPayload
from schemas.paginations import PaginatedResponse, PaginationLinks
from schemas.user import UserReadSchema, UserUpdateSchema
from services.auth import get_current_user
from services.paginations import PaginationHelper

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserReadSchema,
    summary="Get current authenticated user",
    description="Retrieve information about the currently logged-in user.",
)
async def get_me(
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    current_user: Annotated[TokenPayload, Depends(get_current_user())],
) -> User:
    """
    Get details of the currently authenticated user.
    """
    return await crud.get_by_id(current_user.sub_id)


@router.get(
    "/",
    summary="List all users (For ADMINs)",
    description="Retrieve a paginated list of all registered users. Accessible only to administrators.",
)
async def list_users(
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    admin_user: Annotated[TokenPayload, Depends(get_current_user(roles=[UserRole.ADMIN]))],
    limit: Annotated[int, Query(ge=1, le=500, description="Maximum number of users per page")] = 100,
    offset: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
) -> PaginatedResponse[UserReadSchema]:
    """
    Get a paginated list of users.
    **Access restricted to ADMINs.**
    """
    users, total = await crud.get_list(limit=limit, offset=offset)

    pagination: PaginationHelper = PaginationHelper(limit=limit, offset=offset, total=total)
    next_link, prev_link = pagination.get_pagination_links()

    return PaginatedResponse(
        items=TypeAdapter(list[UserReadSchema]).validate_python(users),
        links=PaginationLinks(next=next_link, previous=prev_link, count=total),
    )


@router.get(
    "/{user_id}",
    response_model=UserReadSchema,
    summary="Get user by ID (For ADMINs)",
    description="Retrieve details of a specific user by their unique ID. Accessible only to administrators.",
)
async def get_user(
    user_id: int,
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    admin_user: Annotated[TokenPayload, Depends(get_current_user(roles=[UserRole.ADMIN]))],
) -> User:
    return await crud.get_by_id(user_id)


@router.patch(
    "/",
    response_model=UserReadSchema,
    summary="Update current user",
    description="Update the information of the currently authenticated user.",
)
async def update_user(
    payload: UserUpdateSchema,
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    current_user: Annotated[TokenPayload, Depends(get_current_user())],
) -> User:
    return await crud.update(current_user.sub_id, payload)


@router.delete(
    "/{user_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user by ID (For ADMINs)",
    description="Remove a user from the system by their ID. Accessible only to administrators.",
)
async def delete_user(
    user_id: int,
    crud: Annotated[UserCRUD, Depends(get_user_crud)],
    admin_user: Annotated[TokenPayload, Depends(get_current_user(roles=[UserRole.ADMIN]))],
) -> None:
    await crud.delete(user_id)
    return None
