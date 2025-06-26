from typing import Optional
from app.configs.mappers import MAIN_CATEGORY_NAMES, SUBCATEGORY_NAMES, KILO_MAPPER


class CategoryHelper:
    @staticmethod
    def get_main_category_id_by_name(name: str) -> Optional[str]:
        for k, v in MAIN_CATEGORY_NAMES.items():
            if v == name:
                return k
        return None

    @staticmethod
    def get_subcategory_id_by_name(main_cat_id: str, name: str) -> Optional[str]:
        subcats = SUBCATEGORY_NAMES.get(main_cat_id, {})
        for k, v in subcats.items():
            if v == name:
                return k
        return None

    @staticmethod
    def has_subcategories(main_cat_id: str) -> bool:
        subcats = KILO_MAPPER.get(main_cat_id)
        return not isinstance(subcats, int)

    @staticmethod
    def validate_price(price_text: str) -> tuple[bool, Optional[float]]:
        try:
            price = float(price_text.replace(",", ".").strip())
            if price <= 0:
                return False, None
            return True, price
        except ValueError:
            return False, None

    @staticmethod
    def validate_quantity(quantity_text: str) -> tuple[bool, Optional[int]]:
        try:
            quantity = int(quantity_text.strip())
            if quantity <= 0:
                return False, None
            return True, quantity
        except ValueError:
            return False, None
