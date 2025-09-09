from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationLinks(BaseModel):
    next: str | None = None
    previous: str | None = None
    count: int | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    links: PaginationLinks
