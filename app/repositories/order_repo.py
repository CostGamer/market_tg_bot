from logging import getLogger
from sqlalchemy import select, insert, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pydantic_models import OrderPMGet, OrderPMPost, OrderPMUpdate
from app.models.sql_models import User, Order

logger = getLogger(__name__)


class OrderRepo:
    def __init__(self, con: AsyncSession) -> None:
        self._con = con

    async def get_user_orders(self, tg_id: int) -> list[OrderPMGet] | None:
        query = (
            select(Order)
            .join(User)
            .where(User.tg_id == tg_id)
            .order_by(Order.id.desc())
        )
        result = (await self._con.execute(query)).scalars().all()
        return (
            [OrderPMGet.model_validate(order, from_attributes=True) for order in result]
            if result
            else None
        )

    async def create_order(
        self, tg_id: int, order_data: OrderPMPost
    ) -> OrderPMPost | None:
        query = select(User).where(User.tg_id == tg_id)
        user = (await self._con.execute(query)).scalar_one_or_none()
        if not user:
            return None

        insert_data = order_data.model_dump(exclude_unset=True)
        insert_data["user_id"] = user.id
        result = await self._con.execute(
            insert(Order).values(**insert_data).returning(Order)
        )
        return OrderPMPost.model_validate(result.scalar_one(), from_attributes=True)

    async def update_order_info(
        self, order_data: OrderPMUpdate, order_id: int
    ) -> OrderPMPost:
        update_data = order_data.model_dump(exclude_unset=True)
        query = (
            update(Order)
            .values(**update_data)
            .where(Order.id == order_id)
            .returning(Order)
        )
        res = (await self._con.execute(query)).scalar_one_or_none()
        return OrderPMPost.model_validate(res, from_attributes=True)

    async def get_order_by_id(self, order_id: int):
        query = (
            select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
        )
        result = await self._con.execute(query)
        return result.scalar_one_or_none()

    async def get_order_with_user(self, order_id: int):
        query = (
            select(Order).options(selectinload(Order.user)).where(Order.id == order_id)
        )
        result = await self._con.execute(query)
        return result.scalar_one_or_none()
