from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, func

from app.models.sql_models.sql_base import Base

if TYPE_CHECKING:
    from .sql_address import User
    from .sql_order import Order


class Promocodes(Base):
    __tablename__ = "promocodes"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    promocode: Mapped[str] = mapped_column(nullable=False)
    amount_percentage: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now()
    )
    is_active: Mapped[bool] = mapped_column(nullable=False, default=True)

    user: Mapped["User"] = relationship("User", back_populates="promocodes")
    order: Mapped["Order"] = relationship("Order", back_populates="promocodes")
