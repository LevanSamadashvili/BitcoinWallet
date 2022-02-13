import unittest
from typing import Optional

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
    default_transaction_fee, random_api_key_generator, random_address_generator,
)
from App.runner.api import app, get_core


def get_in_memory_core() -> BitcoinCore:
    return BitcoinCore(
        user_repository=InMemoryUserRepository(),
        wallet_repository=InMemoryWalletRepository(),
        transactions_repository=InMemoryTransactionsRepository(),
        statistics_repository=InMemoryStatisticsRepository(),
        api_key_generator_strategy=random_api_key_generator,
        address_generator_strategy=random_address_generator,
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

    def test_get_balance_invalid(self) -> None:
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = None
        params["address"] = None
        response = client.get(
            "/wallets/{address}",
            headers=params,
        )
        assert response.status_code == 400

    def test_get_balance_invalid_api_key(self) -> None:
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = ""
        params["address"] = None
        response = client.get(
            "/wallets/{address}",
            headers=params,
        )
        assert response.status_code == 404

    def test_get_balance_invalid_wallet(self) -> None:
        self.in_memory_core.user_repository.create_user("tamo1")
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = "tamo1"
        params["address"] = None
        response = client.get(
            "/wallets/{address}",
            headers=params,
        )
        assert response.status_code == 403

    def test_get_balance_not_your_wallet(self) -> None:
        self.in_memory_core.user_repository.create_user("tamo3")
        self.in_memory_core.user_repository.create_user("tamo2")
        self.in_memory_core.wallet_repository.create_wallet(api_key="tamo2", address="tamo22")
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = "tamo3"
        params["address"] = "tamo22"
        response = client.get(
            "/wallets/tamo22",
            headers=params,
        )
        assert response.status_code == 403

    def test_get_balance_successfully(self) -> None:
        self.in_memory_core.user_repository.create_user("tamo4")
        self.in_memory_core.wallet_repository.create_wallet(api_key="tamo4", address="tamo44")
        assert self.in_memory_core.wallet_repository.get_wallet("tamo44") is not None
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = "tamo4"
        response = client.get(
            "/wallets/tamo44",
            headers=params,
        )
        assert response.status_code == 200
        assert response.json()['address'] == "tamo44"
        assert response.json()['balance_usd'] == 0
        assert response.json()['balance_btc'] == 0




