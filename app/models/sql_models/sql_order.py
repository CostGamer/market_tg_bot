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
    from .sql_address import Address


class Order(Base):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"), nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[float] = mapped_column(nullable=False)
    final_price: Mapped[float] = mapped_column(nullable=False)
    product_url: Mapped[str] = mapped_column(nullable=False)
    photo_url: Mapped[str] = mapped_column(nullable=True)
    track_cn: Mapped[str] = mapped_column(nullable=True)
    track_ru: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    address: Mapped["Address"] = relationship("Address", back_populates="orders")
