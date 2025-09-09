from typing import Generic, TypeVar

T = TypeVar("T")


class PaginationHelper(Generic[T]):
    def __init__(self, limit: int, offset: int, total: int):
        self.limit = limit
        self.offset = offset
        self.total = total

    def get_pagination_links(self, base_path: str = "/api/v1/") -> tuple[str | None, str | None]:
        next_link = None
        prev_link = None

        if self.offset + self.limit < self.total:
            next_link = f"{base_path}?offset={self.offset + self.limit}&limit={self.limit}"

        if self.offset > 0:
            prev_offset = max(0, self.offset - self.limit)
            prev_link = f"{base_path}?offset={prev_offset}&limit={self.limit}"

        return next_link, prev_link
