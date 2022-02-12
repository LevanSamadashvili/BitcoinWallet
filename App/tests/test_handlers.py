import unittest
from dataclasses import dataclass
from typing import List
from unittest.mock import MagicMock

from App.core import status
from App.core.bitcoin_core import default_api_key_generator, default_transaction_fee
from App.core.constants import MAX_AVAILABLE_WALLETS
from App.core.core_responses import CoreResponse, RegisterUserResponse, GetStatisticsResponse, \
    GetWalletTransactionsResponse, GetTransactionsResponse, SaveTransactionResponse
from App.core.handlers import (
    CreateUserHandler,
    HasUserHandler,
    IHandle,
    MaxWalletsHandler,
    NoHandler, GetStatisticsHandler, IsAdminHandler, GetWalletTransactionsHandler, GetTransactionHandler,
    SaveTransactionHandler,
)
from App.core.models.statistics import Statistics
from App.core.models.transaction import Transaction
from App.core.models.wallet import Wallet
from App.core.observer import StatisticsObserver
from App.infra.repositories.statistics_repository import InMemoryStatisticsRepository
from App.infra.repositories.transactions_repository import InMemoryTransactionsRepository
from App.infra.repositories.user_repository import InMemoryUserRepository
from App.infra.repositories.wallet_repository import InMemoryWalletRepository


@dataclass
class HandlerForTest(IHandle):
    was_called: bool = False

    def handle(self) -> CoreResponse:
        self.was_called = True
        return CoreResponse(status_code=0)


class TestHandlers(unittest.TestCase):
    def setUp(self) -> None:
        self.user_repository = InMemoryUserRepository()
        self.wallet_repository = InMemoryWalletRepository()
        self.statistics_repository = InMemoryStatisticsRepository()
        self.transactions_repository = InMemoryTransactionsRepository()

        self.test_handler = HandlerForTest()

    def test_no_handler(self) -> None:
        handler = NoHandler()
        response = handler.handle()

        assert response.status_code == 0

    def test_should_create_user(self) -> None:
        handler = CreateUserHandler(
            next_handler=NoHandler(),
            user_repository=self.user_repository,
            api_key_generator_strategy=default_api_key_generator,
        )

        response = handler.handle()
        assert response.status_code == status.USER_CREATED_SUCCESSFULLY
        assert isinstance(response, RegisterUserResponse)
        assert self.user_repository.has_user(api_key=response.api_key)

    def test_should_not_have_user(self) -> None:
        handler = HasUserHandler(
            next_handler=NoHandler(),
            api_key="trash",
            user_repository=self.user_repository,
        )

        response = handler.handle()
        assert response.status_code == status.INCORRECT_API_KEY

    def test_should_have_user(self) -> None:
        api_key = "test_api_key"
        self.user_repository.create_user(api_key=api_key)

        handler = HasUserHandler(
            next_handler=self.test_handler,
            api_key=api_key,
            user_repository=self.user_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    def test_can_create_another_wallet(self) -> None:
        api_key = "test_api_key"
        self.user_repository.create_user(api_key=api_key)

        handler = MaxWalletsHandler(
            next_handler=self.test_handler,
            api_key=api_key,
            wallet_repository=self.wallet_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    def test_cant_create_more_wallets(self) -> None:
        api_key = "test_api_key"
        self.user_repository.create_user(api_key=api_key)

        for i in range(MAX_AVAILABLE_WALLETS):
            self.wallet_repository.create_wallet(address=f"wallet{i}", api_key=api_key)

        handler = MaxWalletsHandler(
            next_handler=NoHandler(),
            api_key=api_key,
            wallet_repository=self.wallet_repository,
        )

        response = handler.handle()
        assert response.status_code == status.CANT_CREATE_MORE_WALLETS

    def test_should_create_wallet(self) -> None:
        pass

    def test_cant_get_statistics(self) -> None:
        self.statistics_repository.get_statistics = MagicMock(return_value=None)

        handler = GetStatisticsHandler(next_handler=NoHandler(),
                                       statistics_repository=self.statistics_repository)

        response = handler.handle()
        assert response.status_code == status.FETCH_STATISTICS_UNSUCCESSFUL

    def test_can_get_statistics(self) -> None:
        statistics = Statistics(num_transactions=11, profit=11)
        self.statistics_repository.get_statistics = MagicMock(return_value=statistics)

        handler = GetStatisticsHandler(next_handler=NoHandler(),
                                       statistics_repository=self.statistics_repository)

        response = handler.handle()
        assert response.status_code == status.FETCH_STATISTICS_SUCCESSFUL
        assert isinstance(response, GetStatisticsResponse)
        assert response.platform_profit == 11
        assert response.total_num_transactions == 11

    def test_invalid_admin_api_key(self) -> None:
        invalid_key = "123"
        handler = IsAdminHandler(next_handler=NoHandler(),
                                 key=invalid_key)
        response = handler.handle()
        assert response.status_code == status.INCORRECT_API_KEY

    def test_valid_admin_api_key(self) -> None:
        invalid_key = "3.14"
        handler = IsAdminHandler(next_handler=self.test_handler,
                                 key=invalid_key)
        handler.handle()
        assert self.test_handler.was_called

    def test_cant_get_wallet_transactions(self) -> None:
        self.transactions_repository.get_wallet_transactions = MagicMock(return_value=None)
        handler = GetWalletTransactionsHandler(next_handler=NoHandler(),
                                               transactions_repository=self.transactions_repository,
                                               address="add")
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_UNSUCCESSFUL

    def test_can_get_wallet_transactions(self) -> None:
        transactions: List[Transaction] = []
        transaction = Transaction(first_address="ad1", second_address="ad2", amount=1.1)
        transactions.append(transaction)
        self.transactions_repository.get_wallet_transactions = MagicMock(return_value=transactions)
        handler = GetWalletTransactionsHandler(next_handler=NoHandler(),
                                               transactions_repository=self.transactions_repository,
                                               address="add")
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_SUCCESSFUL
        assert isinstance(response, GetWalletTransactionsResponse)
        assert response.transactions == transactions

    def test_cant_get_transactions(self) -> None:
        self.transactions_repository.get_all_transactions = MagicMock(return_value=None)
        handler = GetTransactionHandler(next_handler=NoHandler(),
                                        transactions_repository=self.transactions_repository)
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_UNSUCCESSFUL

    def test_can_get_transactions(self) -> None:
        transactions: List[Transaction] = []
        transaction = Transaction(first_address="ad1", second_address="ad2", amount=1.1)
        transactions.append(transaction)
        self.transactions_repository.get_all_transactions = MagicMock(return_value=transactions)
        handler = GetTransactionHandler(next_handler=NoHandler(),
                                        transactions_repository=self.transactions_repository)
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_SUCCESSFUL
        assert isinstance(response, GetTransactionsResponse)
        assert response.transactions == transactions

    def test_cant_save_transaction_invalid_wallet(self) -> None:
        self.wallet_repository.get_wallet = MagicMock(return_value=None)
        handler = SaveTransactionHandler(next_handler=NoHandler(),
                                         transactions_repository=self.transactions_repository,
                                         wallet_repository=self.wallet_repository,
                                         first_address="1",
                                         second_address="2",
                                         btc_amount=1.1,
                                         statistics_repository=self.statistics_repository,
                                         statistics_observer=StatisticsObserver(),
                                         transaction_fee_strategy=default_transaction_fee)
        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    def test_should_save_transaction(self) -> None:
        wallet = Wallet(address="1", api_key="1", balance_btc=10.0)
        self.wallet_repository.get_wallet = MagicMock(return_value=wallet)
        handler = SaveTransactionHandler(next_handler=NoHandler(),
                                         transactions_repository=self.transactions_repository,
                                         wallet_repository=self.wallet_repository,
                                         first_address="1",
                                         second_address="2",
                                         btc_amount=1.1,
                                         statistics_repository=self.statistics_repository,
                                         statistics_observer=StatisticsObserver(),
                                         transaction_fee_strategy=default_transaction_fee)
        response = handler.handle()
        assert response.status_code == status.TRANSACTION_SUCCESSFUL
        assert isinstance(response, SaveTransactionResponse)
