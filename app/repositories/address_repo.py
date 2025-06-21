from logging import getLogger

from sqlalchemy import select, update, insert, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pydantic_models import AddressPM, AddressPMGet
from app.models.sql_models import Address, User

logger = getLogger(__name__)


class AddressRepo:
    def __init__(self, con: AsyncSession) -> None:
        self._con = con

    async def get_user_addresses(self, tg_id: int) -> list[AddressPMGet] | None:
        query = select(Address).join(User).where(User.tg_id == tg_id)
        result = (await self._con.execute(query)).scalars().all()
        return (
            [AddressPMGet.model_validate(addr, from_attributes=True) for addr in result]
            if result
            else None
        )

    async def create_address(
        self, tg_id: int, address_data: AddressPM
    ) -> AddressPM | None:
        query = select(User).where(User.tg_id == tg_id)
        user = (await self._con.execute(query)).scalar_one_or_none()

        if not user:
            return None

        insert_data = address_data.model_dump(exclude_unset=True)
        insert_data["user_id"] = user.id

        result = await self._con.execute(
            insert(Address).values(**insert_data).returning(Address)
        )
        return AddressPM.model_validate(result.scalar_one(), from_attributes=True)

    async def update_address(
        self, address_id: int, address_data: AddressPM
    ) -> AddressPM | None:
        update_data = address_data.model_dump(exclude_unset=True)

        result = await self._con.execute(
            update(Address)
            .where(Address.id == address_id)
            .values(**update_data)
            .returning(Address)
        )
        return (
            AddressPM.model_validate(result.scalar_one(), from_attributes=True)
            if result
            else None
        )

    async def delete_address(self, address_id: int) -> bool:
        result = await self._con.execute(
            delete(Address).where(Address.id == address_id)
        )
        return result.rowcount > 0

    async def get_address_by_id(self, address_id: int) -> AddressPMGet:
        query = select(Address).where(Address.id == address_id)
        result = (await self._con.execute(query)).scalar_one()
        return AddressPMGet.model_validate(result, from_attributes=True)
