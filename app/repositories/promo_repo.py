from logging import getLogger

from sqlalchemy import select, update, insert, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pydantic_models import PromoGetPM
from app.models.sql_models import User, Promocodes

logger = getLogger(__name__)


class PromoRepo:
    def __init__(self, con: AsyncSession) -> None:
        self._con = con

    async def get_active_user_promos(self, tg_id: int) -> list[PromoGetPM] | None:
        query = (
            select(Promocodes)
            .join(User)
            .where(and_(User.tg_id == tg_id, Promocodes.is_active))
        )
        result = (await self._con.execute(query)).scalars().all()
        return (
            [PromoGetPM.model_validate(promo, from_attributes=True) for promo in result]
            if result
            else None
        )

    async def create_promo(self, tg_id: int, promo: str, percentage: int) -> int | None:
        user_query = select(User).where(User.tg_id == tg_id)
        user_result = await self._con.execute(user_query)
        user = user_result.scalar_one_or_none()

        if not user:
            return None

        query = (
            insert(Promocodes)
            .values(promocode=promo, amount_percentage=percentage, user_id=user.id)
            .returning(Promocodes.id)
        )
        res = (await self._con.execute(query)).scalar_one()
        return res

    async def update_promo_status(self, promo: str) -> None:
        query = (
            update(Promocodes).values(active=True).where(Promocodes.promocode == promo)
        )
        await self._con.execute(query)
