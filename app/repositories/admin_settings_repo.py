from logging import getLogger

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pydantic_models import AdminSettingsPM
from app.models.sql_models import AdminSettings

logger = getLogger(__name__)


class AdminSettingsRepo:
    def __init__(self, con: AsyncSession) -> None:
        self._con = con

    async def get_settings(self) -> AdminSettingsPM:
        query = select(AdminSettings).limit(1)
        result = (await self._con.execute(query)).scalar_one_or_none()
        return AdminSettingsPM.model_validate(result)

    async def update_settings(self, settings: AdminSettingsPM) -> AdminSettingsPM:
        query = (
            update(AdminSettings)
            .values(**settings.model_dump())
            .returning(AdminSettings)
        )
        res = (await self._con.execute(query)).scalar_one_or_none()
        return AdminSettingsPM.model_validate(res)
