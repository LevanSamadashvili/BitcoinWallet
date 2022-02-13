import unittest
from dataclasses import dataclass
from typing import Callable
from unittest import mock
from unittest.mock import MagicMock

from App.core import status
from App.core.bitcoin_core import default_api_key_generator, default_transaction_fee
from App.core.constants import INITIAL_BITCOINS_WALLET, MAX_AVAILABLE_WALLETS
from App.core.core_responses import (
    CoreResponse,
    CreateWalletResponse,
    GetBalanceResponse,
    GetStatisticsResponse,
    GetTransactionsResponse,
    GetWalletTransactionsResponse,
    RegisterUserResponse,
    SaveTransactionResponse,
)
from App.core.handlers import (
    CreateUserHandler,
    CreateWalletHandler,
    GetStatisticsHandler,
    GetTransactionHandler,
    GetWalletHandler,
    GetWalletTransactionsHandler,
    HasUserHandler,
    HasWalletHandler,
    IHandle,
    IsAdminHandler,
    MakeTransactionHandler,
    MaxWalletsHandler,
    NoHandler,
    SaveTransactionHandler,
    TransactionValidationHandler,
)
from App.core.models.statistics import Statistics
from App.core.models.transaction import Transaction
from App.core.models.wallet import Wallet
from App.core.observer import StatisticsObserver
from App.infra.repositories.statistics_repository import InMemoryStatisticsRepository
from App.infra.repositories.transactions_repository import (
    InMemoryTransactionsRepository,
)
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

    @mock.patch(
        "App.infra.repositories.user_repository.InMemoryUserRepository.create_user",
        mock.MagicMock(return_value=True),
    )
    def test_should_create_user(self) -> None:
        key_gen: Callable[[], str] = lambda: "1"

        handler = CreateUserHandler(
            next_handler=NoHandler(),
            user_repository=self.user_repository,
            api_key_generator_strategy=key_gen,
        )

        response = handler.handle()
        assert response.status_code == status.USER_CREATED_SUCCESSFULLY
        assert isinstance(response, RegisterUserResponse)
        assert response.api_key == key_gen()

    @mock.patch(
        "App.infra.repositories.user_repository.InMemoryUserRepository.create_user",
        mock.MagicMock(return_value=False),
    )
    def test_should_not_create_user(self) -> None:
        handler = CreateUserHandler(
            next_handler=NoHandler(),
            user_repository=self.user_repository,
            api_key_generator_strategy=default_api_key_generator,
        )

        response = handler.handle()
        assert response.status_code == status.USER_REGISTRATION_ERROR

    @mock.patch(
        "App.infra.repositories.user_repository.InMemoryUserRepository.has_user",
        mock.MagicMock(return_value=False),
    )
    def test_should_not_have_user(self) -> None:
        handler = HasUserHandler(
            next_handler=NoHandler(),
            api_key="trash",
            user_repository=self.user_repository,
        )

        response = handler.handle()
        assert response.status_code == status.INCORRECT_API_KEY

    @mock.patch(
        "App.infra.repositories.user_repository.InMemoryUserRepository.has_user",
        mock.MagicMock(return_value=True),
    )
    def test_should_have_user(self) -> None:
        handler = HasUserHandler(
            next_handler=self.test_handler,
            api_key="api_key",
            user_repository=self.user_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_num_wallets",
        mock.MagicMock(return_value=0),
    )
    def test_can_create_another_wallet(self) -> None:
        handler = MaxWalletsHandler(
            next_handler=self.test_handler,
            api_key="api_key",
            wallet_repository=self.wallet_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_num_wallets",
        mock.MagicMock(return_value=MAX_AVAILABLE_WALLETS),
    )
    def test_cant_create_more_wallets(self) -> None:
        handler = MaxWalletsHandler(
            next_handler=NoHandler(),
            api_key="api_key",
            wallet_repository=self.wallet_repository,
        )

        response = handler.handle()
        assert response.status_code == status.CANT_CREATE_MORE_WALLETS

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.deposit_btc",
        mock.MagicMock(return_value=True),
    )
    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.create_wallet",
        mock.MagicMock(return_value=True),
    )
    def test_should_create_wallet(self) -> None:
        address_generator: Callable[[], str] = lambda: "1"
        btc_usd_convertor: Callable[[float], float] = lambda x: 2 * x

        handler = CreateWalletHandler(
            next_handler=NoHandler(),
            api_key="api_key",
            wallet_repository=self.wallet_repository,
            address_generator_strategy=address_generator,
            btc_usd_convertor=btc_usd_convertor,
        )

        response = handler.handle()
        assert isinstance(response, CreateWalletResponse)
        assert response.address == address_generator()
        assert response.balance_usd == btc_usd_convertor(INITIAL_BITCOINS_WALLET)
        assert response.balance_btc == INITIAL_BITCOINS_WALLET

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.create_wallet",
        mock.MagicMock(return_value=False),
    )
    def test_should_not_create_wallet(self) -> None:
        handler = CreateWalletHandler(
            next_handler=NoHandler(),
            api_key="api_key",
            wallet_repository=self.wallet_repository,
            address_generator_strategy=(lambda: "1"),
            btc_usd_convertor=(lambda x: x),
        )

        response = handler.handle()
        assert response.status_code == status.WALLET_CREATION_ERROR

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_wallet",
        mock.MagicMock(return_value=None),
    )
    def test_should_not_get_wallet(self) -> None:
        handler = GetWalletHandler(
            next_handler=NoHandler(),
            address="random",
            wallet_repository=self.wallet_repository,
            btc_usd_convertor=(lambda x: x),
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_wallet",
        mock.MagicMock(
            return_value=Wallet(api_key="api", address="dzmaddress", balance_btc=0.35)
        ),
    )
    def test_should_get_wallet(self) -> None:
        btc_usd: Callable[[float], float] = lambda x: 2 * x
        handler = GetWalletHandler(
            next_handler=NoHandler(),
            address="dzmf",
            wallet_repository=self.wallet_repository,
            btc_usd_convertor=btc_usd,
        )

        response = handler.handle()
        assert isinstance(response, GetBalanceResponse)
        assert response.status_code == status.GOT_BALANCE_SUCCESSFULLY
        assert response.balance_btc == 0.35
        assert response.balance_usd == btc_usd(response.balance_btc)
        assert response.address == "dzmaddress"

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_balance",
        mock.MagicMock(return_value=0.36),
    )
    def test_enough_money(self) -> None:
        handler = TransactionValidationHandler(
            next_handler=self.test_handler,
            address="random",
            btc_amount=0.3,
            wallet_repository=self.wallet_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_balance",
        mock.MagicMock(return_value=0.36),
    )
    def test_not_enough_money(self) -> None:
        handler = TransactionValidationHandler(
            next_handler=self.test_handler,
            address="random",
            btc_amount=1.0,
            wallet_repository=self.wallet_repository,
        )

        response = handler.handle()
        assert response.status_code == status.TRANSACTION_UNSUCCESSFUL

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.has_wallet",
        mock.MagicMock(return_value=True),
    )
    def test_should_have_wallet(self) -> None:
        handler = HasWalletHandler(
            next_handler=self.test_handler,
            address="address",
            wallet_repository=self.wallet_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.has_wallet",
        mock.MagicMock(return_value=False),
    )
    def test_should_not_have_wallet(self) -> None:
        handler = HasWalletHandler(
            next_handler=NoHandler(),
            address="random",
            wallet_repository=self.wallet_repository,
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_wallet",
        MagicMock(return_value=None),
    )
    def test_should_not_make_transaction_no_wallets(self) -> None:
        handler = MakeTransactionHandler(
            next_handler=NoHandler(),
            first_wallet_address="first_wallet_address",
            second_wallet_address="second_wallet_address",
            btc_amount=1.0,
            wallet_repository=self.wallet_repository,
            transaction_fee_strategy=(lambda w1, w2: 0.0),
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.withdraw_btc",
        MagicMock(return_value=False),
    )
    def test_should_not_make_transaction_first_cant_pay(self) -> None:
        first_wallet_address = "first_address"
        second_wallet_address = "second_address"

        self.wallet_repository.create_wallet(
            address=first_wallet_address, api_key="key_1"
        )
        self.wallet_repository.create_wallet(
            address=second_wallet_address, api_key="key_2"
        )

        handler = MakeTransactionHandler(
            next_handler=NoHandler(),
            first_wallet_address=first_wallet_address,
            second_wallet_address=second_wallet_address,
            btc_amount=1.0,
            wallet_repository=self.wallet_repository,
            transaction_fee_strategy=(lambda w1, w2: 0.0),
        )

        response = handler.handle()
        assert response.status_code == status.TRANSACTION_UNSUCCESSFUL

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.deposit_btc",
        MagicMock(return_value=False),
    )
    def test_should_not_make_transaction_cant_deposit_to_second(self) -> None:
        first_wallet_address = "first_address"
        second_wallet_address = "second_address"

        self.wallet_repository.create_wallet(
            address=first_wallet_address, api_key="key_1"
        )
        self.wallet_repository.create_wallet(
            address=second_wallet_address, api_key="key_2"
        )

        handler = MakeTransactionHandler(
            next_handler=NoHandler(),
            first_wallet_address=first_wallet_address,
            second_wallet_address=second_wallet_address,
            btc_amount=3.0,
            wallet_repository=self.wallet_repository,
            transaction_fee_strategy=(lambda w1, w2: 0.0),
        )

        response = handler.handle()
        assert response.status_code == status.TRANSACTION_UNSUCCESSFUL

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_wallet",
        MagicMock(return_value=Wallet(api_key="dd", address="mm", balance_btc=10.0)),
    )
    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.withdraw_btc",
        MagicMock(return_value=True),
    )
    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.deposit_btc",
        MagicMock(return_value=True),
    )
    def test_should_make_transaction(self) -> None:
        handler = MakeTransactionHandler(
            next_handler=self.test_handler,
            first_wallet_address="first_wallet_address",
            second_wallet_address="second_wallet_address",
            btc_amount=3.0,
            wallet_repository=self.wallet_repository,
            transaction_fee_strategy=(lambda w1, w2: 0.0),
        )

        handler.handle()
        assert self.test_handler.was_called

    @mock.patch(
        "App.infra.repositories.statistics_repository.InMemoryStatisticsRepository.get_statistics",
        MagicMock(return_value=None),
    )
    def test_cant_get_statistics(self) -> None:
        handler = GetStatisticsHandler(
            next_handler=NoHandler(), statistics_repository=self.statistics_repository
        )

        response = handler.handle()
        assert response.status_code == status.FETCH_STATISTICS_UNSUCCESSFUL

    @mock.patch(
        "App.infra.repositories.statistics_repository.InMemoryStatisticsRepository.get_statistics",
        MagicMock(return_value=Statistics(num_transactions=11, profit=11)),
    )
    def test_can_get_statistics(self) -> None:
        handler = GetStatisticsHandler(
            next_handler=NoHandler(), statistics_repository=self.statistics_repository
        )

        response = handler.handle()
        assert response.status_code == status.FETCH_STATISTICS_SUCCESSFUL
        assert isinstance(response, GetStatisticsResponse)
        assert response.platform_profit == 11
        assert response.total_num_transactions == 11

    def test_invalid_admin_api_key(self) -> None:
        invalid_key = "123"
        handler = IsAdminHandler(next_handler=NoHandler(), key=invalid_key)
        response = handler.handle()
        assert response.status_code == status.INCORRECT_API_KEY

    def test_valid_admin_api_key(self) -> None:
        invalid_key = "3.14"
        handler = IsAdminHandler(next_handler=self.test_handler, key=invalid_key)
        handler.handle()
        assert self.test_handler.was_called

    @mock.patch(
        "App.infra.repositories.transactions_repository.InMemoryTransactionsRepository.get_wallet_transactions",
        MagicMock(return_value=None),
    )
    def test_cant_get_wallet_transactions(self) -> None:
        handler = GetWalletTransactionsHandler(
            next_handler=NoHandler(),
            transactions_repository=self.transactions_repository,
            address="add",
        )
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_UNSUCCESSFUL

    @mock.patch(
        "App.infra.repositories.transactions_repository.InMemoryTransactionsRepository.get_wallet_transactions",
        MagicMock(
            return_value=[
                Transaction(first_address="ad1", second_address="ad2", amount=1.1)
            ]
        ),
    )
    def test_can_get_wallet_transactions(self) -> None:
        transactions: list[Transaction] = []
        transaction = Transaction(first_address="ad1", second_address="ad2", amount=1.1)
        transactions.append(transaction)

        handler = GetWalletTransactionsHandler(
            next_handler=NoHandler(),
            transactions_repository=self.transactions_repository,
            address="add",
        )
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_SUCCESSFUL
        assert isinstance(response, GetWalletTransactionsResponse)
        assert response.transactions == transactions

    @mock.patch(
        "App.infra.repositories.transactions_repository.InMemoryTransactionsRepository.get_all_transactions",
        MagicMock(return_value=None),
    )
    def test_cant_get_transactions(self) -> None:
        handler = GetTransactionHandler(
            next_handler=NoHandler(),
            transactions_repository=self.transactions_repository,
        )
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_UNSUCCESSFUL

    @mock.patch(
        "App.infra.repositories.transactions_repository.InMemoryTransactionsRepository.get_all_transactions",
        MagicMock(
            return_value=[
                Transaction(first_address="ad1", second_address="ad2", amount=1.1)
            ]
        ),
    )
    def test_can_get_transactions(self) -> None:
        transactions: list[Transaction] = []
        transaction = Transaction(first_address="ad1", second_address="ad2", amount=1.1)
        transactions.append(transaction)

        handler = GetTransactionHandler(
            next_handler=NoHandler(),
            transactions_repository=self.transactions_repository,
        )
        response = handler.handle()
        assert response.status_code == status.FETCH_TRANSACTIONS_SUCCESSFUL
        assert isinstance(response, GetTransactionsResponse)
        assert response.transactions == transactions

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_wallet",
        MagicMock(return_value=None),
    )
    def test_cant_save_transaction_invalid_wallet(self) -> None:
        handler = SaveTransactionHandler(
            next_handler=NoHandler(),
            transactions_repository=self.transactions_repository,
            wallet_repository=self.wallet_repository,
            first_address="1",
            second_address="2",
            btc_amount=1.1,
            statistics_repository=self.statistics_repository,
            statistics_observer=StatisticsObserver(),
            transaction_fee_strategy=default_transaction_fee,
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    @mock.patch(
        "App.infra.repositories.wallet_repository.InMemoryWalletRepository.get_wallet",
        MagicMock(return_value=Wallet(address="1", api_key="1", balance_btc=10.0)),
    )
    def test_should_save_transaction(self) -> None:
        handler = SaveTransactionHandler(
            next_handler=NoHandler(),
            transactions_repository=self.transactions_repository,
            wallet_repository=self.wallet_repository,
            first_address="1",
            second_address="2",
            btc_amount=1.1,
            statistics_repository=self.statistics_repository,
            statistics_observer=StatisticsObserver(),
            transaction_fee_strategy=default_transaction_fee,
        )
        response = handler.handle()
        assert response.status_code == status.TRANSACTION_SUCCESSFUL
        assert isinstance(response, SaveTransactionResponse)
