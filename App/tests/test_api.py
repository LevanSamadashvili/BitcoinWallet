import unittest

from fastapi.testclient import TestClient

from App.core.bitcoin_core import BitcoinCore
from App.infra.btc_usd import default_btc_usd_convertor
from App.infra.repositories.statistics_repository import InMemoryStatisticsRepository
from App.infra.repositories.transactions_repository import (
    InMemoryTransactionsRepository,
)
from App.infra.repositories.user_repository import InMemoryUserRepository
from App.infra.repositories.wallet_repository import InMemoryWalletRepository
from App.infra.strategies import (
    default_address_generator,
    default_api_key_generator,
    default_transaction_fee,
)
from App.runner.api import app, get_core


def get_in_memory_core() -> BitcoinCore:
    return BitcoinCore(
        user_repository=InMemoryUserRepository(),
        wallet_repository=InMemoryWalletRepository(),
        transactions_repository=InMemoryTransactionsRepository(),
        statistics_repository=InMemoryStatisticsRepository(),
        api_key_generator_strategy=default_api_key_generator,
        address_generator_strategy=default_address_generator,
        btc_usd_convertor_strategy=default_btc_usd_convertor,
        transaction_fee_strategy=default_transaction_fee,
    )


app.dependency_overrides[get_core] = get_in_memory_core

client = TestClient(app)


class TestApi(unittest.TestCase):
    def setUp(self) -> None:
        self.in_memory_core = get_in_memory_core()

    def test_register_user(self) -> None:
        response = client.post(
            "/users",
        )
        print(response)
        assert response.status_code == 201

    def test_get_transactions(self) -> None:
        self.in_memory_core.user_repository.create_user("user1")
        response = client.get(
            "/transactions",
            headers={"api-key": "user1"}
        )
        assert response.status_code == 200
        assert len(response.json()['transactions']) == 0

        self.in_memory_core.transactions_repository.add_transaction('address1', 'address2', 4.0)
        self.in_memory_core.transactions_repository.add_transaction('address2', 'address1', 2.0)
        response = client.get(
            "/transactions",
            headers={"api-key": "user1"}
        )
        print(response.reason)
        assert response.status_code == 200
        assert len(response.json()['transactions']) == 2

        response = client.get(
            "/transactions",
            headers={"api-key": "user2"}
        )
        assert response.status_code == 404
