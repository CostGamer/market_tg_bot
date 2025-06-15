from app.configs import all_settings
import aiohttp
from app.repositories import AdminSettingsRepo

from app.configs.mappers import KILO_MAPPER


class PriceCalculator:
    CB_RF_URL = all_settings.different.cb_rf_url

    def __init__(self, price: float, admin_settings_repo: AdminSettingsRepo) -> None:
        self.price = price
        self.admin_settings_repo = admin_settings_repo

    async def calculate_price(
        self,
        cny_amount: float,
        category: str,
    ) -> tuple[float, float | None]:
        fee = None

        admin_settings = await self.admin_settings_repo.get_settings()

        cny_rate, eur_rate = await self.get_cny_eur_rates()
        check_over_limit = await self.is_over_limit(cny_amount, cny_rate, eur_rate)

        if check_over_limit:
            fee = await self.calculate_fee(cny_amount, cny_rate, eur_rate)
            total_price = (
                self.price * (cny_rate + admin_settings.cny_rate_syrcharge)
            ) + fee
        else:
            total_price = self.price * (cny_rate + admin_settings.cny_rate_syrcharge)

        get_kilos = KILO_MAPPER.get(category, 1)
        total_price += get_kilos * admin_settings.kilo_delivery

        return total_price * admin_settings.commision_rate, fee

    async def get_cny_eur_rates(self) -> tuple[float, float]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.CB_RF_URL) as resp:
                data = await resp.json(content_type=None)
                cny = data["Valute"]["CNY"]["Value"]
                eur = data["Valute"]["EUR"]["Value"]
                return float(cny), float(eur)

    async def is_over_limit(
        self,
        cny_amount: float,
        cny_rate: float,
        eur_rate: float,
        reserve: float = 0.03,
    ) -> bool:
        limit_rub = 200 * eur_rate * (1 - reserve)
        user_rub = cny_amount * cny_rate
        return user_rub > limit_rub

    async def cny_to_eur(
        self,
        cny_amount: float,
        cny_rate: float,
        eur_rate: float,
    ) -> float:
        return cny_amount * cny_rate / eur_rate

    async def calculate_fee(
        self,
        cny_amount: float,
        cny_rate: float,
        eur_rate: float,
    ) -> float:
        cny_amount_in_eur = await self.cny_to_eur(cny_amount, cny_rate, eur_rate)
        difference_amount_standart = cny_amount_in_eur - 200

        first_fee = difference_amount_standart * 0.15 * eur_rate
        second_fee = 500  # административный сбор
        third_fee = (first_fee + second_fee) * 0.05  # комиссия таможенного агента

        final_fee = first_fee + second_fee + third_fee
        return final_fee
