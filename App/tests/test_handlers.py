from dataclasses import dataclass

from App.core.bitcoin_core import default_api_key_generator
from App.core.constants import MAX_AVAILABLE_WALLETS
from App.core.core_responses import RegisterUserResponse, CoreResponse
from App.core.handlers import CreateUserHandler, NoHandler, IHandle, HasUserHandler, MaxWalletsHandler
from App.infra.repositories.user_repository import InMemoryUserRepository

from App.core import status
from App.infra.repositories.wallet_repository import InMemoryWalletRepository


@dataclass
class HandlerForTest(IHandle):
    was_called: bool = False

    def handle(self) -> CoreResponse:
        self.was_called = True
        return CoreResponse(status_code=0)


def test_no_handler() -> None:
    handler = NoHandler()
    response = handler.handle()

    assert response.status_code == 0

def test_should_create_user() -> None:
    user_repo = InMemoryUserRepository()
    handler = CreateUserHandler(next_handler=NoHandler(),
                                user_repository=user_repo,
                                api_key_generator_strategy=default_api_key_generator)

    response = handler.handle()
    assert response.status_code == status.USER_CREATED_SUCCESSFULLY
    assert isinstance(response, RegisterUserResponse)
    assert user_repo.has_user(api_key=response.api_key)


def test_should_not_have_user() -> None:
    user_repo = InMemoryUserRepository()

    handler = HasUserHandler(next_handler=NoHandler(),
                             api_key="trash",
                             user_repository=user_repo)

    response = handler.handle()
    assert response.status_code == status.INCORRECT_API_KEY


def test_should_have_user() -> None:
    api_key = "test_api_key"
    user_repo = InMemoryUserRepository()
    user_repo.create_user(api_key=api_key)

    next_handler = HandlerForTest()

    handler = HasUserHandler(next_handler=next_handler,
                             api_key=api_key,
                             user_repository=user_repo)

    handler.handle()
    assert next_handler.was_called


def test_can_create_another_wallet() -> None:
    user_repo = InMemoryUserRepository()
    wallet_repo = InMemoryWalletRepository()

    api_key = "test_api_key"
    user_repo.create_user(api_key=api_key)

    next_handler = HandlerForTest()
    handler = MaxWalletsHandler(next_handler=next_handler,
                                api_key=api_key,
                                wallet_repository=wallet_repo)

    handler.handle()
    assert next_handler.was_called

def test_cant_create_more_wallets() -> None:
    user_repo = InMemoryUserRepository()
    wallet_repo = InMemoryWalletRepository()

    api_key = "test_api_key"
    user_repo.create_user(api_key=api_key)

    for i in range(MAX_AVAILABLE_WALLETS):
        wallet_repo.create_wallet(address=f"wallet{i}", api_key=api_key)

    handler = MaxWalletsHandler(next_handler=NoHandler(),
                                api_key=api_key,
                                wallet_repository=wallet_repo)

    response = handler.handle()
    assert response.status_code == status.CANT_CREATE_MORE_WALLETS

