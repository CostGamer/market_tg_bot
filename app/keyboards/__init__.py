from .categories import get_main_categories_keyboard, get_subcategories_keyboard
from .profile import get_profile_keyboard, get_edit_profile_keyboard
from .address import (
    get_address_manage_keyboard,
    get_addresses_keyboard,
    get_edit_address_field_keyboard,
)
from .support import get_support_faq_keyboard
from .order import (
    get_quantity_keyboard,
    get_send_order_keyboard,
    get_yes_no_keyboard,
    get_comment_or_send_keyboard,
    get_cancel_keyboard,
    get_addresses_keyboard_order,
)
from .categories_reply import (
    get_main_categories_keyboard_reply,
    get_subcategories_keyboard_reply,
)
from .admin_order import create_order_status_keyboard

__all__ = [
    "get_profile_keyboard",
    "get_edit_profile_keyboard",
    "get_address_manage_keyboard",
    "get_addresses_keyboard",
    "get_edit_address_field_keyboard",
    "get_main_categories_keyboard",
    "get_quantity_keyboard",
    "get_send_order_keyboard",
    "get_yes_no_keyboard",
    "get_comment_or_send_keyboard",
    "get_subcategories_keyboard",
    "get_support_faq_keyboard",
    "get_main_categories_keyboard_reply",
    "get_addresses_keyboard_order",
    "get_cancel_keyboard",
    "create_order_status_keyboard",
    "get_subcategories_keyboard_reply",
]
