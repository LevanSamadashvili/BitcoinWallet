import unittest
from dataclasses import dataclass

from App.core import status
from App.core.bitcoin_core import default_api_key_generator
from App.core.constants import MAX_AVAILABLE_WALLETS
from App.core.core_responses import CoreResponse, RegisterUserResponse
from App.core.handlers import (
    CreateUserHandler,
    HasUserHandler,
    IHandle,
    MaxWalletsHandler,
    NoHandler,
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
