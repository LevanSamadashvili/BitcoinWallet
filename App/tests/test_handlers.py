import unittest
from dataclasses import dataclass
from typing import Callable
from unittest.mock import MagicMock

from App.core import status
from App.core.bitcoin_core import default_api_key_generator
from App.core.constants import INITIAL_BITCOINS_WALLET, MAX_AVAILABLE_WALLETS
from App.core.core_responses import (
    CoreResponse,
    CreateWalletResponse,
    GetBalanceResponse,
    RegisterUserResponse,
)
from App.core.handlers import (
    CreateUserHandler,
    CreateWalletHandler,
    GetWalletHandler,
    HasUserHandler,
    HasWalletHandler,
    IHandle,
    MakeTransactionHandler,
    MaxWalletsHandler,
    NoHandler,
    TransactionValidationHandler,
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

    def test_should_not_create_user(self) -> None:
        handler = CreateUserHandler(
            next_handler=NoHandler(),
            user_repository=self.user_repository,
            api_key_generator_strategy=default_api_key_generator,
        )

        self.user_repository.create_user = MagicMock(return_value=False)
        response = handler.handle()
        assert response.status_code == status.USER_REGISTRATION_ERROR

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
        api_key = "test_api_key"
        self.user_repository.create_user(api_key=api_key)

        address_generator: Callable[[], str] = lambda: "1"
        btc_usd_convertor: Callable[[float], float] = lambda x: 2 * x

        handler = CreateWalletHandler(
            next_handler=NoHandler(),
            api_key=api_key,
            wallet_repository=self.wallet_repository,
            address_generator_strategy=address_generator,
            btc_usd_convertor=btc_usd_convertor,
        )

        response = handler.handle()
        assert isinstance(response, CreateWalletResponse)
        assert response.address == address_generator()
        assert response.balance_usd == btc_usd_convertor(INITIAL_BITCOINS_WALLET)
        assert self.wallet_repository.has_wallet(address=address_generator())

    def test_should_not_create_wallet(self) -> None:
        self.wallet_repository.create_wallet = MagicMock(return_value=False)

        handler = CreateWalletHandler(
            next_handler=NoHandler(),
            api_key="api_key",
            wallet_repository=self.wallet_repository,
            address_generator_strategy=(lambda: "1"),
            btc_usd_convertor=(lambda x: x),
        )

        response = handler.handle()
        assert response.status_code == status.WALLET_CREATION_ERROR

    def test_should_not_get_wallet(self) -> None:
        handler = GetWalletHandler(
            next_handler=NoHandler(),
            address="random",
            wallet_repository=self.wallet_repository,
            btc_usd_convertor=(lambda x: x),
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    def test_should_get_wallet(self) -> None:
        api_key = "test_api_key"
        address = "address"

        self.user_repository.create_user(api_key=api_key)
        self.wallet_repository.create_wallet(address=address, api_key=api_key)

        btc_usd: Callable[[float], float] = lambda x: 2 * x
        handler = GetWalletHandler(
            next_handler=NoHandler(),
            address=address,
            wallet_repository=self.wallet_repository,
            btc_usd_convertor=btc_usd,
        )

        response = handler.handle()
        assert isinstance(response, GetBalanceResponse)
        assert response.status_code == status.GOT_BALANCE_SUCCESSFULLY
        assert response.balance_btc == 0.0
        assert response.balance_usd == btc_usd(response.balance_btc)
        assert response.address == address
        assert self.wallet_repository.has_wallet(address=address)

    def test_enough_money(self) -> None:
        api_key = "test_api_key"
        address = "address"

        self.user_repository.create_user(api_key=api_key)
        self.wallet_repository.create_wallet(address=address, api_key=api_key)

        self.wallet_repository.deposit_btc(address=address, btc_amount=1.0)

        handler = TransactionValidationHandler(
            next_handler=self.test_handler,
            address=address,
            btc_amount=0.3,
            wallet_repository=self.wallet_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    def test_not_enough_money(self) -> None:
        api_key = "test_api_key"
        address = "address"

        self.user_repository.create_user(api_key=api_key)
        self.wallet_repository.create_wallet(address=address, api_key=api_key)

        handler = TransactionValidationHandler(
            next_handler=self.test_handler,
            address=address,
            btc_amount=1.0,
            wallet_repository=self.wallet_repository,
        )

        response = handler.handle()
        assert response.status_code == status.TRANSACTION_UNSUCCESSFUL

    def test_should_have_wallet(self) -> None:
        address = "address"
        self.wallet_repository.create_wallet(address=address, api_key="api_key")

        handler = HasWalletHandler(
            next_handler=self.test_handler,
            address=address,
            wallet_repository=self.wallet_repository,
        )

        handler.handle()
        assert self.test_handler.was_called

    def test_should_not_have_wallet(self) -> None:
        handler = HasWalletHandler(
            next_handler=NoHandler(),
            address="random",
            wallet_repository=self.wallet_repository,
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    def test_should_not_make_transaction_no_wallets(self) -> None:
        handler = MakeTransactionHandler(
            next_handler=NoHandler(),
            first_wallet_address="random",
            second_wallet_address="second_random",
            btc_amount=1.0,
            wallet_repository=self.wallet_repository,
            transaction_fee_strategy=(lambda w1, w2: 0.0),
        )

        response = handler.handle()
        assert response.status_code == status.INVALID_WALLET

    def test_should_not_make_transaction_first_cant_pay(self) -> None:
        self.wallet_repository.withdraw_btc = MagicMock(return_value=False)

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

    def test_should_not_make_transaction_cant_deposit_to_second(self) -> None:
        pass

    def test_should_make_transaction(self) -> None:
        pass
