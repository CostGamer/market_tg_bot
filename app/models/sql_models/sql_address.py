from typing import TYPE_CHECKING
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import ForeignKey

from app.models.sql_models.sql_base import Base

if TYPE_CHECKING:
    from .sql_user import User
    from .sql_order import Order


class Address(Base):
    __tablename__ = "addresses"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    address: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="addresses")
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="address", cascade="all, delete-orphan"
    )
