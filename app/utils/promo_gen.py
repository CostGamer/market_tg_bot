import random
import string


def generate_promo_code(length=10):
    characters = string.ascii_uppercase + string.digits
    promo_code = "".join(random.choice(characters) for _ in range(length))
    return promo_code
