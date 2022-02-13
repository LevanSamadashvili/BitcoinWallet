import random
import string

from App.core import constants
from App.core.models.wallet import Wallet


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
    chars = string.ascii_letters + string.digits
    address = "".join(random.choice(chars) for i in range(constants.API_KEY_LENGTH))
    return address


def default_transaction_fee(first_wallet: Wallet, second_wallet: Wallet) -> float:
    transaction_fee = 1.5
    if first_wallet.api_key == second_wallet.api_key:
        transaction_fee = 0

    return transaction_fee
