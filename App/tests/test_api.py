import unittest

from fastapi.testclient import TestClient

from App.core.bitcoin_core import BitcoinCore
from App.core.constants import MAX_AVAILABLE_WALLETS
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
        assert response.status_code == 201

    def test_should_create_wallet(self) -> None:
        self.in_memory_core.user_repository.create_user(api_key="api_key")

        response = client.post("/wallets", headers={
            "api-key": "api_key"
        })

        data = response.json()

        assert response.status_code == 201
        assert "address" in data
        assert data["balance_btc"] == 1.0
        assert data["balance_usd"] == self.in_memory_core.btc_usd_convertor_strategy(1.0)
        assert self.in_memory_core.wallet_repository.has_wallet(address=data["address"])

    def test_should_not_create_more_than_max_wallets(self) -> None:
        self.in_memory_core.user_repository.create_user(api_key="api_key")

        for i in range(MAX_AVAILABLE_WALLETS + 3):
            response = client.post("/wallets", headers={
                "api-key": "api_key"
            })

            data = response.json()

            if i >= MAX_AVAILABLE_WALLETS:
                assert response.status_code == 403
                assert "address" not in data
                assert "balance_btc" not in data
                assert "balance_usd" not in data
            else:
                assert response.status_code == 201
                assert "address" in data
                assert data["balance_btc"] == 1.0
                assert data["balance_usd"] == self.in_memory_core.btc_usd_convertor_strategy(1.0)
                assert self.in_memory_core.wallet_repository.has_wallet(address=data["address"])

    def test_create_wallet_api_key_is_none(self) -> None:
        response = client.post("/wallets", headers={
            "api-key": None
        })

        assert response.status_code == 400



