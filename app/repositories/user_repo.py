from logging import getLogger
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.pydantic_models import UserPM
from app.models.sql_models import User
from sqlalchemy.exc import IntegrityError

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

    async def create_user_with_tg_id(
        self, tg_id: int, tg_username: str | None = None
    ) -> UserPM | None:
        try:
            insert_data = {"tg_id": tg_id}
            if tg_username:
                insert_data["tg_username"] = tg_username  # type: ignore
            query = insert(User).values(**insert_data).returning(User)
            result = (await self._con.execute(query)).scalar_one()
            return UserPM.model_validate(result)
        except IntegrityError:
            logger.info(f"Пользователь {tg_id} уже существует")
            await self._con.rollback()
            return None
        except Exception as e:
            logger.error(f"Ошибка создания пользователя {tg_id}: {e}")
            await self._con.rollback()
            raise

    async def update_username(
        self, tg_id: int, tg_username: str | None = None
    ) -> UserPM | None:
        query = (
            update(User)
            .values(tg_username=tg_username)
            .where(User.tg_id == tg_id)
            .returning(User)
        )
        result = (await self._con.execute(query)).scalar_one_or_none()
        return UserPM.model_validate(result) if result else None

    async def upsert_user_basic_info(
        self, tg_id: int, tg_username: str | None = None
    ) -> UserPM | None:
        existing_user = await self.get_user_info(tg_id)

        if existing_user:
            if existing_user.tg_username != tg_username:
                updated_user = await self.update_username(tg_id, tg_username)
                return updated_user if updated_user else existing_user
            return existing_user
        else:
            new_user = await self.create_user_with_tg_id(tg_id, tg_username)
            if new_user:
                return new_user
            else:
                return await self.get_user_info(tg_id)

    async def post_user_tg_id(self, user_tg_id: int) -> None:
        """Устаревший метод - используйте create_user_with_tg_id"""
        await self.create_user_with_tg_id(user_tg_id)
