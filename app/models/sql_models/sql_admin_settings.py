from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.models.sql_models.sql_base import Base


class AdminSettings(Base):
    __tablename__ = "admin_settings"

    commision_rate: Mapped[float] = mapped_column(nullable=False)
    kilo_delivery: Mapped[float] = mapped_column(nullable=False)
    cny_rate_syrcharge: Mapped[float] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False, server_default=func.now(), onupdate=func.now()
    )
    user_tg_id: Mapped[int] = mapped_column(nullable=False, unique=True)
    additional_control: Mapped[int] = mapped_column(nullable=False)
    faq: Mapped[str] = mapped_column(nullable=True)
