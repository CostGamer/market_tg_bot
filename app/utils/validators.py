import re


def is_valid_phone(phone: str) -> bool:
    phone = (
        phone.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if re.fullmatch(r"\+\d{10,15}", phone):
        return True
    if re.fullmatch(r"[78]\d{10}", phone):
        return True
    return False
