from logging import getLogger
from app.configs import all_settings
from app.repositories import AdminSettingsRepo
from app.services.common_service import CommonService
from app.configs.mappers import KILO_MAPPER


logger = getLogger(__name__)


class PriceCalculator(CommonService):
    CB_RF_URL = all_settings.different.cb_rf_url

    def __init__(self, price: float, admin_settings_repo: AdminSettingsRepo) -> None:
        super().__init__(admin_settings_repo)
        self.price = price

    async def calculate_price(
        self, cny_amount: float, category: str, subcategory: str | None = None
    ) -> tuple[float, float | None]:
        fee = None

        admin_settings = await self.admin_settings_repo.get_settings()

        cny_rate, eur_rate = await self.get_cny_eur_rates()
        check_over_limit = await self.is_over_limit(cny_amount, cny_rate, eur_rate)

        if check_over_limit:
            fee = await self.calculate_fee(cny_amount, cny_rate, eur_rate)
            total_price = (
                (self.price * (cny_rate + admin_settings.cny_rate_syrcharge))
                + fee
                + admin_settings.additional_control
            )
        else:
            total_price = (
                self.price * (cny_rate + admin_settings.cny_rate_syrcharge)
                + admin_settings.additional_control
            )

        if subcategory:
            get_kilos = KILO_MAPPER[category][subcategory]
        else:
            get_kilos = KILO_MAPPER[category]

        total_price += get_kilos * admin_settings.kilo_delivery
        return total_price * admin_settings.commision_rate, fee

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
