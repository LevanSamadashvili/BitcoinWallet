import random
import string

from App.core import constants


def default_api_key_generator() -> str:
    return "1"


def default_address_generator() -> str:
    return "1"


def random_address_generator() -> str:
    address = "".join(
        random.choice(string.ascii_lowercase) for i in range(constants.ADDRESS_LENGTH)
    )
    return address


def random_api_key_generator() -> str:
    chars = string.ascii_letters + string.digits + string.punctuation
    address = "".join(random.choice(chars) for i in range(constants.API_KEY_LENGTH))
    return address
