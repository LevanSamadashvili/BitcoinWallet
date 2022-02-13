from App.core import constants
from App.infra.strategies import random_address_generator, random_api_key_generator


def test_address_generator() -> None:
    add = random_address_generator()
    assert len(add) == constants.ADDRESS_LENGTH


def test_api_key_generator() -> None:
    add = random_api_key_generator()
    assert len(add) == constants.API_KEY_LENGTH

