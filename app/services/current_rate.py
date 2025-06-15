from app.configs import all_settings
from app.repositories import AdminSettingsRepo
from app.services.common_service import CommonService


class CurrentRate(CommonService):
    CB_RF_URL = all_settings.different.cb_rf_url

    def __init__(self, admin_settings_repo: AdminSettingsRepo) -> None:
        super().__init__(admin_settings_repo)

    async def current_rate(
        self,
    ) -> float:
        cny_rate, _ = await self.get_cny_eur_rates()
        admin_settings = await self.admin_settings_repo.get_settings()

        return cny_rate + admin_settings.cny_rate_syrcharge
