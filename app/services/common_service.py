from app.configs import all_settings
import aiohttp
from app.repositories import AdminSettingsRepo


class CommonService:
    CB_RF_URL = all_settings.different.cb_rf_url

    def __init__(self, admin_settings_repo: AdminSettingsRepo) -> None:
        self.admin_settings_repo = admin_settings_repo

    async def get_cny_eur_rates(self) -> tuple[float, float]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.CB_RF_URL) as resp:
                data = await resp.json(content_type=None)
                cny = data["Valute"]["CNY"]["Value"]
                eur = data["Valute"]["EUR"]["Value"]
                return float(cny), float(eur)
