from typing import TYPE_CHECKING
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)
from sqlalchemy import ForeignKey, text, DECIMAL

from app.models.sql_models.sql_base import Base

if TYPE_CHECKING:
    from .sql_user import User
    from .sql_address import Address
    from .sql_promocodes import Promocodes


class Order(Base):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    address_id: Mapped[int] = mapped_column(ForeignKey("addresses.id"), nullable=False)
    description: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price_rmb: Mapped[float] = mapped_column(
        DECIMAL(precision=18, scale=2), nullable=False, server_default=text("0")
    )
    unit_price_rub: Mapped[float] = mapped_column(
        DECIMAL(precision=18, scale=2), nullable=False, server_default=text("0")
    )
    final_price: Mapped[float] = mapped_column(
        DECIMAL(precision=18, scale=2), nullable=False
    )
    product_url: Mapped[str] = mapped_column(nullable=False)
    photo_url: Mapped[str] = mapped_column(nullable=True)
    track_cn: Mapped[str] = mapped_column(nullable=True)
    track_ru: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=False)
    promocode_id: Mapped[int] = mapped_column(
        ForeignKey("promocodes.id"), nullable=True
    )

    user: Mapped["User"] = relationship("User", back_populates="orders")
    address: Mapped["Address"] = relationship("Address", back_populates="orders")
    promocode: Mapped["Promocodes"] = relationship("Promocodes", back_populates="order")
