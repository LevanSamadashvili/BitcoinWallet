import unittest
from typing import Optional
from unittest import mock

from fastapi.testclient import TestClient

from App.core import constants
from App.core.bitcoin_core import BitcoinCore
from App.core.constants import INITIAL_BITCOINS_WALLET, MAX_AVAILABLE_WALLETS
from App.infra.btc_usd import default_btc_usd_convertor
from App.infra.repositories.statistics_repository import InMemoryStatisticsRepository
from App.infra.repositories.transactions_repository import (
    InMemoryTransactionsRepository,
)
from App.infra.repositories.user_repository import InMemoryUserRepository
from App.infra.repositories.wallet_repository import InMemoryWalletRepository
from App.infra.strategies import (
    default_transaction_fee,
    random_address_generator,
    random_api_key_generator,
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
        assert response.status_code == 201

    def test_should_create_wallet(self) -> None:
        api_key = "levani_api_key"
        self.in_memory_core.user_repository.create_user(api_key=api_key)

        response = client.post("/wallets", headers={"api-key": api_key})

        data = response.json()

        assert response.status_code == 201
        assert "address" in data
        assert data["balance_btc"] == INITIAL_BITCOINS_WALLET
        assert data["balance_usd"] == self.in_memory_core.btc_usd_convertor_strategy(
            INITIAL_BITCOINS_WALLET
        )
        assert self.in_memory_core.wallet_repository.has_wallet(address=data["address"])

    def test_should_not_create_more_than_max_wallets(self) -> None:
        api_key = "levani_api_key_2"
        self.in_memory_core.user_repository.create_user(api_key=api_key)

        for i in range(MAX_AVAILABLE_WALLETS + 1):
            response = client.post("/wallets", headers={"api-key": api_key})

            data = response.json()

            if i >= MAX_AVAILABLE_WALLETS:
                assert response.status_code == 403
            else:
                assert response.status_code == 201
                assert "address" in data
                assert data["balance_btc"] == 1.0
                assert data[
                    "balance_usd"
                ] == self.in_memory_core.btc_usd_convertor_strategy(1.0)
                assert self.in_memory_core.wallet_repository.has_wallet(
                    address=data["address"]
                )

    def test_create_wallet_api_key_is_none(self) -> None:
        response = client.post("/wallets", headers={"api-key": None})

        assert response.status_code == 400

    def test_create_wallet_user_doesnt_exist(self) -> None:
        api_key = "levani_api_key_3"

        response = client.post("/wallets", headers={"api-key": api_key})

        assert response.status_code == 404

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.create_wallet",
        mock.MagicMock(return_value=False),
    )
    def test_create_wallet_creation_error(self) -> None:
        api_key = "levani_api_key_4"
        self.in_memory_core.user_repository.create_user(api_key=api_key)

        response = client.post("/wallets", headers={"api-key": api_key})

        assert response.status_code == 500

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

        response = client.get(
            "/wallets/random_address",
            headers=params,
        )
        assert response.status_code == 403

    def test_get_balance_not_your_wallet(self) -> None:
        self.in_memory_core.user_repository.create_user("tamo3")
        self.in_memory_core.user_repository.create_user("tamo2")
        self.in_memory_core.wallet_repository.create_wallet(
            api_key="tamo2", address="tamo22"
        )
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = "tamo3"

        response = client.get(
            "/wallets/tamo22",
            headers=params,
        )
        assert response.status_code == 403

    def test_get_balance_successfully(self) -> None:
        self.in_memory_core.user_repository.create_user("tamo4")
        self.in_memory_core.wallet_repository.create_wallet(
            api_key="tamo4", address="tamo44"
        )
        assert self.in_memory_core.wallet_repository.get_wallet("tamo44") is not None
        params: dict[str, Optional[str]] = dict()
        params["api-key"] = "tamo4"
        response = client.get(
            "/wallets/tamo44",
            headers=params,
        )
        assert response.status_code == 200
        assert response.json()["address"] == "tamo44"
        assert response.json()["balance_usd"] == 0
        assert response.json()["balance_btc"] == 0

    def test_get_transactions(self) -> None:
        self.in_memory_core.user_repository.create_user("user1")
        response = client.get("/transactions", headers={"api-key": "user1"})
        assert response.status_code == 200
        assert len(response.json()["transactions"]) == 0

        self.in_memory_core.transactions_repository.add_transaction(
            "address1", "wallet2", 4.0
        )
        self.in_memory_core.transactions_repository.add_transaction(
            "wallet2", "address1", 2.0
        )
        response = client.get("/transactions", headers={"api-key": "user1"})
        assert response.status_code == 200
        assert len(response.json()["transactions"]) == 2

        response = client.get("/transactions", headers={"api-key": "user2"})
        assert response.status_code == 404

    def test_cant_get_transactions_api_key_is_none(self) -> None:
        response = client.get("/transactions", headers={"api-key": None})

        assert response.status_code == 400

    @mock.patch(
        "App.infra.repositories.transactions_repository.InMemoryTransactionsRepository.get_all_transactions",
        mock.MagicMock(return_value=None),
    )
    def test_cant_fetch_transactions_internal_error(self) -> None:
        self.in_memory_core.user_repository.create_user(api_key="user3")
        response = client.get("/transactions", headers={"api-key": "user3"})

        assert response.status_code == 500

    def test_get_wallet_transactions(self) -> None:
        self.in_memory_core.user_repository.create_user("user4")
        self.in_memory_core.wallet_repository.create_wallet("wallet1", "user4")
        response = client.get(
            "/wallets/wallet1/transactions",
            headers={"api-key": "user4", "address": "wallet1"},
        )
        assert response.status_code == 200
        assert len(response.json()["transactions"]) == 0

        self.in_memory_core.transactions_repository.add_transaction(
            "wallet1", "wallet2", 4.0
        )
        self.in_memory_core.transactions_repository.add_transaction(
            "wallet3", "wallet2", 4.0
        )
        response = client.get(
            "/wallets/wallet1/transactions",
            headers={"api-key": "user4", "address": "wallet1"},
        )
        assert response.status_code == 200
        assert len(response.json()["transactions"]) == 1

        response = client.get(
            "/wallets/wallet2/transactions",
            headers={"api-key": "user4", "address": "wallet2"},
        )
        assert response.status_code == 403

    def test_cant_get_wallet_transactions_api_key_is_none(self) -> None:
        response = client.get(
            "/wallets/wallet1/transactions",
            headers={"api-key": None, "address": None},
        )

        assert response.status_code == 400

    def test_cant_get_wallet_transactions_user_doesnt_exist(self) -> None:
        response = client.get(
            "/wallets/wallet1/transactions",
            headers={"api-key": "some_random_api_key_123123_", "address": "addre"},
        )

        assert response.status_code == 404

    @mock.patch(
        "App.infra.repositories.transactions_repository.InMemoryTransactionsRepository.get_wallet_transactions",
        mock.MagicMock(return_value=None),
    )
    def test_cant_get_wallet_transactions_internal_error(self) -> None:
        self.in_memory_core.user_repository.create_user("user5")
        self.in_memory_core.wallet_repository.create_wallet("wallet1", "user5")

        response = client.get(
            "/wallets/wallet1/transactions",
            headers={"api-key": "user5", "address": "wallet1"},
        )

        assert response.status_code == 500

    def test_get_statistics(self) -> None:
        response = client.get(
            "/statistics", headers={"admin-api-key": constants.ADMIN_API_KEY}
        )
        assert response.status_code == 200
        assert response.json()["total_num_transactions"] == 0
        assert response.json()["platform_profit"] == 0

        self.in_memory_core.statistics_repository.add_statistic(
            num_new_transactions=10, profit=35.135
        )

        response = client.get(
            "/statistics", headers={"admin-api-key": constants.ADMIN_API_KEY}
        )

        assert response.status_code == 200
        assert response.json()["total_num_transactions"] == 10
        assert response.json()["platform_profit"] == 35.135

    def test_cant_get_statistics_api_key_is_none(self) -> None:
        response = client.get("/statistics", headers={"admin-api-key": None})

        assert response.status_code == 400

    def test_cant_get_statistics_invalid_user(self) -> None:
        response = client.get("/statistics", headers={"admin-api-key": "user7"})

        assert response.status_code == 404

    @mock.patch(
        "App.infra.repositories.statistics_repository.InMemoryStatisticsRepository.get_statistics",
        mock.MagicMock(return_value=None),
    )
    def test_cant_get_statistics_internal_error(self) -> None:
        response = client.get(
            "/statistics", headers={"admin-api-key": constants.ADMIN_API_KEY}
        )

        assert response.status_code == 500
