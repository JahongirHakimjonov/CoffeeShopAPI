from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, declarative_mixin, mapped_column


@declarative_mixin
class BaseMixin:
    created_at: Mapped[datetime] = mapped_column(
        default=func.now(), nullable=False, comment="Creation timestamp of the table"
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Last update timestamp of the table",
    )
