from sqlalchemy.orm import DeclarativeBase

from db.meta import meta


class AbstractBase(DeclarativeBase):
    """Base for all models."""

    metadata = meta
    __abstract__ = True

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={getattr(self, 'id', None)})>"

    def __str__(self) -> str:
        return self.__repr__()
