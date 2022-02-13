from dataclasses import dataclass
from typing import Callable

from App.core.core_requests import (
    CreateWalletRequest,
    GetBalanceRequest,
    GetStatisticsRequest,
    GetTransactionsRequest,
    GetWalletTransactionsRequest,
    MakeTransactionRequest,
    RegisterUserRequest,
)
from App.core.core_responses import CoreResponse
from App.core.handlers import (
    CreateUserHandler,
    CreateWalletHandler,
    GetStatisticsHandler,
    GetTransactionHandler,
    GetWalletHandler,
    GetWalletTransactionsHandler,
    HasUserHandler,
    HasWalletHandler,
    IsAdminHandler,
    MakeTransactionHandler,
    MaxWalletsHandler,
    NoHandler,
    SaveTransactionHandler,
    TransactionValidationHandler,
    WalletBelongsToUserHandler,
)
from App.core.models.wallet import Wallet
from App.core.observer import StatisticsObserver
from App.core.repository_interfaces.statistics_repository import IStatisticsRepository
from App.core.repository_interfaces.transactions_repository import (
    ITransactionsRepository,
)
from App.core.repository_interfaces.user_repository import IUserRepository
from App.core.repository_interfaces.wallet_repository import IWalletRepository


@dataclass
class BitcoinCore:
    user_repository: IUserRepository
    wallet_repository: IWalletRepository
    transactions_repository: ITransactionsRepository
    statistics_repository: IStatisticsRepository

    api_key_generator_strategy: Callable[[], str]
    address_generator_strategy: Callable[[], str]
    btc_usd_convertor_strategy: Callable[[float], float]
    transaction_fee_strategy: Callable[[Wallet, Wallet], float]

    def register_user(self, _: RegisterUserRequest) -> CoreResponse:
        handler = CreateUserHandler(
            next_handler=NoHandler(),
            user_repository=self.user_repository,
            api_key_generator_strategy=self.api_key_generator_strategy,
        )

        return handler.handle()

    def create_wallet(self, request: CreateWalletRequest) -> CoreResponse:
        handler = HasUserHandler(
            MaxWalletsHandler(
                CreateWalletHandler(
                    NoHandler(),
                    api_key=request.api_key,
                    wallet_repository=self.wallet_repository,
                    address_generator_strategy=self.address_generator_strategy,
                    btc_usd_convertor=self.btc_usd_convertor_strategy,
                ),
                api_key=request.api_key,
                wallet_repository=self.wallet_repository,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )

        return handler.handle()

    def get_balance(self, request: GetBalanceRequest) -> CoreResponse:
        handler = HasUserHandler(
            next_handler=WalletBelongsToUserHandler(
                next_handler=GetWalletHandler(
                    next_handler=NoHandler(),
                    address=request.address,
                    wallet_repository=self.wallet_repository,
                    btc_usd_convertor=self.btc_usd_convertor_strategy,
                ),
                api_key=request.api_key,
                address=request.address,
                wallet_repository=self.wallet_repository,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )

        return handler.handle()

    def make_transaction(self, request: MakeTransactionRequest) -> CoreResponse:
        handler = HasUserHandler(
            next_handler=HasWalletHandler(
                next_handler=WalletBelongsToUserHandler(
                    next_handler=HasWalletHandler(
                        next_handler=TransactionValidationHandler(
                            next_handler=MakeTransactionHandler(
                                next_handler=SaveTransactionHandler(
                                    next_handler=NoHandler(),
                                    first_address=request.first_wallet_address,
                                    second_address=request.second_wallet_address,
                                    btc_amount=request.btc_amount,
                                    wallet_repository=self.wallet_repository,
                                    transactions_repository=self.transactions_repository,
                                    statistics_repository=self.statistics_repository,
                                    statistics_observer=StatisticsObserver(),
                                    transaction_fee_strategy=self.transaction_fee_strategy,
                                ),
                                first_wallet_address=request.first_wallet_address,
                                second_wallet_address=request.second_wallet_address,
                                btc_amount=request.btc_amount,
                                wallet_repository=self.wallet_repository,
                                transaction_fee_strategy=self.transaction_fee_strategy,
                            ),
                            address=request.first_wallet_address,
                            btc_amount=request.btc_amount,
                            wallet_repository=self.wallet_repository,
                        ),
                        address=request.second_wallet_address,
                        wallet_repository=self.wallet_repository,
                    ),
                    address=request.first_wallet_address,
                    api_key=request.api_key,
                    wallet_repository=self.wallet_repository,
                ),
                address=request.first_wallet_address,
                wallet_repository=self.wallet_repository,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )

        return handler.handle()

    def get_transactions(self, request: GetTransactionsRequest) -> CoreResponse:

        handler = HasUserHandler(
            next_handler=GetTransactionHandler(
                next_handler=NoHandler(),
                transactions_repository=self.transactions_repository,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )
        return handler.handle()

    def get_wallet_transactions(
        self, request: GetWalletTransactionsRequest
    ) -> CoreResponse:

        handler = HasUserHandler(
            next_handler=HasWalletHandler(
                next_handler=WalletBelongsToUserHandler(
                    next_handler=GetWalletTransactionsHandler(
                        next_handler=NoHandler(),
                        transactions_repository=self.transactions_repository,
                        address=request.address,
                    ),
                    address=request.address,
                    api_key=request.api_key,
                    wallet_repository=self.wallet_repository,
                ),
                address=request.address,
                wallet_repository=self.wallet_repository,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )
        return handler.handle()

    def get_statistics(self, request: GetStatisticsRequest) -> CoreResponse:
        handler = IsAdminHandler(
            next_handler=GetStatisticsHandler(
                next_handler=NoHandler(),
                statistics_repository=self.statistics_repository,
            ),
            key=request.api_key,
        )
        return handler.handle()
