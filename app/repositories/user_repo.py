from logging import getLogger

from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pydantic_models import UserPM
from app.models.sql_models import User

logger = getLogger(__name__)


class UserRepo:
    def __init__(self, con: AsyncSession) -> None:
        self._con = con

    async def get_user_info(self, tg_id: int) -> UserPM | None:
        query = select(User).where(User.tg_id == tg_id)
        result = (await self._con.execute(query)).scalar_one_or_none()
        return UserPM.model_validate(result) if result else None

    async def update_user_info(self, user_data: UserPM) -> UserPM:
        update_data = user_data.model_dump(exclude={"tg_id"}, exclude_unset=True)

        query = (
            update(User)
            .values(**update_data)
            .where(User.tg_id == user_data.tg_id)
            .returning(User)
        )
        res = (await self._con.execute(query)).scalar_one_or_none()
        return UserPM.model_validate(res)

    async def post_user(self, user_data: UserPM) -> UserPM:
        insert_data = user_data.model_dump(exclude_unset=True)

        query = insert(User).values(**insert_data).returning(User)
        res = (await self._con.execute(query)).scalar_one()
        return UserPM.model_validate(res)
