import bcrypt
from pydantic import EmailStr
from sqlalchemy import BigInteger, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import String

from core.constants.role import UserRole
from db.base import AbstractBase
from db.models.base import BaseMixin


class User(AbstractBase, BaseMixin):
    __tablename__ = "custom_user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    email: Mapped[EmailStr] = mapped_column(String(255), unique=True, nullable=False, index=True)
    first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False),
        index=True,
        nullable=False,
        default=UserRole.USER,
    )
    is_verified: Mapped[bool] = mapped_column(nullable=False, default=False)

    async def set_password(self, password: str) -> None:
        """
        Hash and set the user's password.
        """
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        self.password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    async def check_password(self, password: str) -> bool:
        """
        Verify if the provided password matches the stored hashed password.
        """
        try:
            return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))
        except (ValueError, AttributeError):
            return False

    def __repr__(self) -> str:
        return f"<User id={self.id}, email={self.email}, role={self.role}>"
