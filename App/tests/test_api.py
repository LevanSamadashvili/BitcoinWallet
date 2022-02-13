import unittest
from unittest import mock

from fastapi.testclient import TestClient

from App.core.bitcoin_core import BitcoinCore
from App.core.models.wallet import Wallet
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
        assert "api_key" in response.json()

    @mock.patch(
        "App.infra.repositories.user_repository.InMemoryUserRepository.create_user",
        mock.MagicMock(return_value=False),
    )
    def test_create_user_failed(self) -> None:
        response = client.post(
            "/users",
        )
        assert response.status_code == 500
        assert "api_key" not in response.json()

    def test_make_transaction_validation(self) -> None:
        response = client.post(
            "/transactions",
            json={"api-key": None,
                  "first-wallet-address": "test",
                  "second-wallet-address": "test",
                  "btc-amount": 0
                  },
        )
        assert response.status_code == 400
        response = client.post(
            "/transactions",
            json={"api-key": "None",
                  "first-wallet-address": None,
                  "second-wallet-address": "None",
                  "btc-amount": 0
                  },
        )
        assert response.status_code == 400
        response = client.post(
            "/transactions",
            json={"api-key": "None",
                  "first-wallet-address": "None",
                  "second-wallet-address": None,
                  "btc-amount": 0
                  },
        )
        assert response.status_code == 400
        response = client.post(
            "/transactions",
            json={"api-key": "None",
                  "first-wallet-address": "None",
                  "second-wallet-address": "None",
                  "btc-amount": None
                  },
        )
        assert response.status_code == 400


    def test_make_transaction_successful_transaction(self) -> None:
        api_key = "nini_api_key"
        self.in_memory_core.user_repository.create_user(api_key=api_key)
        first_wallet = "nini_first_wallet"
        second_wallet = "nini_second_wallet"
        wallet_first = Wallet(api_key=api_key, address=first_wallet, balance_btc=10)
        wallet_second = Wallet(api_key=api_key, address=second_wallet, balance_btc=0)

        self.in_memory_core.wallet_repository.create_wallet(address=first_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.create_wallet(address=second_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.deposit_btc(address=first_wallet, btc_amount=10)
        btc_amount = 2
        response = client.post(
            "/transactions",
            headers={"api-key": api_key,
                     "first-wallet-address": first_wallet,
                     "second-wallet-address": second_wallet,
                     "btc-amount": "2"
                     },
        )
        updated_balance = btc_amount*(1 - self.in_memory_core.transaction_fee_strategy(wallet_first, wallet_second))
        assert response.status_code == 200
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(first_wallet), 8)
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(second_wallet), updated_balance)
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(address=first_wallet)) > 0
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(address=second_wallet)) > 0
        assert self.in_memory_core.transactions_repository.get_wallet_transactions(address=second_wallet)[0] \
                   .amount == 2
        assert self.in_memory_core.transactions_repository.get_wallet_transactions(address=first_wallet)[0] \
                   .amount == 2

    def test_make_transactions_wallet_doesnt_exist(self) -> None:
        api_key = "nini_api_key1"
        self.in_memory_core.user_repository.create_user(api_key=api_key)
        first_wallet = "nini_first_wallet1"
        second_wallet = "nini_second_wallet2"

        self.in_memory_core.wallet_repository.create_wallet(address=first_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.deposit_btc(address=first_wallet, btc_amount=10)
        response = client.post(
            "/transactions",
            headers={"api-key": api_key,
                     "first-wallet-address": first_wallet,
                     "second-wallet-address": second_wallet,
                     "btc-amount": "2"
                     },
        )
        assert response.status_code == 403
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(first_wallet), 10)
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(address=first_wallet)) == 0

        response = client.post(
            "/transactions",
            headers={"api-key": api_key,
                     "first-wallet-address": second_wallet,
                     "second-wallet-address": first_wallet,
                     "btc-amount": "2"
                     },
        )
        assert response.status_code == 403
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(first_wallet), 10)
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(address=first_wallet)) == 0

    def test_make_transaction_invalid_api_key(self) -> None:
        api_key = "nini_api_key2"
        self.in_memory_core.user_repository.create_user(api_key=api_key)
        first_wallet = "nini_first_wallet"
        second_wallet = "nini_second_wallet"

        self.in_memory_core.wallet_repository.create_wallet(address=first_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.create_wallet(address=second_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.deposit_btc(address=first_wallet, btc_amount=5)
        response = client.post(
            "/transactions",
            headers={"api-key": "api_key3",
                     "first-wallet-address": first_wallet,
                     "second-wallet-address": second_wallet,
                     "btc-amount": "2"
                     },
        )
        assert response.status_code == 404
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(first_wallet), 5)
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(second_wallet), 0)
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(address=first_wallet)) == 0
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(address=second_wallet)) == 0

    def test_make_transaction_not_enough_money(self) -> None:
        api_key = "nini_api_key3"
        self.in_memory_core.user_repository.create_user(api_key=api_key)
        first_wallet = "nini_first_wallet_1"
        second_wallet = "nini_second_wallet_2"

        self.in_memory_core.wallet_repository.create_wallet(address=first_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.create_wallet(address=second_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.deposit_btc(address=first_wallet, btc_amount=4)
        response = client.post(
            "/transactions",
            headers={"api-key": api_key,
                     "first-wallet-address": first_wallet,
                     "second-wallet-address": second_wallet,
                     "btc-amount": "5"
                     },
        )
        assert response.status_code == 452
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(first_wallet), 4)
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(second_wallet), 0)
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(first_wallet)) == 0
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(second_wallet)) == 0

    def test_make_transaction_unsuccessful(self) -> None:
        api_key = "nini_api_key4"
        second_api_key = "nini_api_key_5"
        self.in_memory_core.user_repository.create_user(api_key=api_key)
        self.in_memory_core.user_repository.create_user(api_key=second_api_key)
        first_wallet = "nini_first_wallet_111"
        second_wallet = "nini_second_wallet_211"
        wallet_first = Wallet(api_key=api_key, address=first_wallet, balance_btc=10)
        wallet_second = Wallet(api_key=second_api_key, address=second_wallet, balance_btc=2)
        self.in_memory_core.wallet_repository.create_wallet(address=first_wallet, api_key=api_key)
        self.in_memory_core.wallet_repository.create_wallet(address=second_wallet, api_key=second_api_key)
        self.in_memory_core.wallet_repository.deposit_btc(address=first_wallet, btc_amount=10)
        self.in_memory_core.wallet_repository.deposit_btc(address=second_wallet, btc_amount=2)
        print(self.in_memory_core.wallet_repository.get_balance(first_wallet))
        btc_amount = 1
        response = client.post(
            "/transactions",
            headers={"api-key": api_key,
                     "first-wallet-address": first_wallet,
                     "second-wallet-address": second_wallet,
                     "btc-amount": "1"
                     },
        )
        updated_balance = 2 + btc_amount*(1-self.in_memory_core.transaction_fee_strategy(wallet_first, wallet_second)/100)
        assert response.status_code == 200
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(first_wallet),
                               9)
        self.assertAlmostEqual(self.in_memory_core.wallet_repository.get_balance(second_wallet), updated_balance)
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(first_wallet)) > 0
        assert len(self.in_memory_core.transactions_repository.get_wallet_transactions(second_wallet)) > 0
