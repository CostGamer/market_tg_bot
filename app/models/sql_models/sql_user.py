from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import BigInteger

from app.models.sql_models.sql_base import Base

if TYPE_CHECKING:
    from .sql_address import Address
    from .sql_order import Order
    from .sql_promocodes import Promocodes


class User(Base):
    __tablename__ = "users"

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(nullable=True)
    phone: Mapped[str] = mapped_column(nullable=True)
    tg_username: Mapped[str] = mapped_column(nullable=True)
    last_game_time: Mapped[datetime] = mapped_column(
        nullable=True,
    )

    addresses: Mapped[list["Address"]] = relationship(
        "Address", back_populates="user", cascade="all, delete-orphan", uselist=True
    )
    orders: Mapped[list["Order"]] = relationship(
        "Order", back_populates="user", cascade="all, delete-orphan", uselist=True
    )
    promocodes: Mapped[list["Promocodes"]] = relationship(
        "Promocodes", back_populates="user", cascade="all, delete-orphan", uselist=True
    )
