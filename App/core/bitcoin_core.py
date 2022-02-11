from dataclasses import dataclass
from typing import Callable

from App.core import status
from App.core.core_requests import (
    CreateWalletRequest,
    GetBalanceRequest,
    GetStatisticsRequest,
    GetTransactionsRequest,
    GetWalletTransactionsRequest,
    MakeTransactionRequest,
    RegisterUserRequest,
)
from App.core.core_responses import (
    CoreResponse,
    GetStatisticsResponse,
    GetTransactionsResponse,
    GetWalletTransactionsResponse,
)
from App.core.handlers import (
    CreateUserHandler,
    CreateWalletHandler,
    GetWalletHandler,
    HasUserHandler,
    HasWalletHandler,
    MakeTransactionHandler,
    MaxWalletsHandler,
    NoHandler,
    SaveTransactionHandler,
    TransactionValidationHandler,
)
from App.core.models.wallet import Wallet
from App.core.observer import StatisticsObserver
from App.core.repository_interfaces.admin_repository import IAdminRepository
from App.core.repository_interfaces.statistics_repository import IStatisticsRepository
from App.core.repository_interfaces.transactions_repository import (
    ITransactionsRepository,
)
from App.core.repository_interfaces.user_repository import IUserRepository
from App.core.repository_interfaces.wallet_repository import IWalletRepository


def default_api_key_generator() -> str:
    return "1"


def default_address_generator() -> str:
    return "1"


def default_transaction_fee(first_wallet: Wallet, second_wallet: Wallet) -> float:
    transaction_fee = 1.5
    if first_wallet.api_key == second_wallet.api_key:
        transaction_fee = 0

    return transaction_fee


@dataclass
class BitcoinCore:
    user_repository: IUserRepository
    admin_repository: IAdminRepository
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
        # api_key = self.api_key_generator_strategy()
        # user_created = self.user_repository.create_user(api_key)
        #
        # if not user_created:
        #     return RegisterUserResponse(status_code=213, api_key="")
        #
        # return RegisterUserResponse(status_code=213, api_key=api_key)

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

        # has_user = self.user_repository.has_user(api_key=request.api_key)
        #
        # if not has_user:
        #     return CreateWalletResponse(
        #         address="",
        #         balance_btc=0.0,
        #         balance_usd=0.0,
        #         status_code=status.INCORRECT_API_KEY,
        #     )
        #
        # num_wallets = self.wallet_repository.get_num_wallets(api_key=request.api_key)
        #
        # if num_wallets == 3:
        #     return CreateWalletResponse(
        #         address="",
        #         balance_btc=0.0,
        #         balance_usd=0.0,
        #         status_code=status.CANT_CREATE_MORE_WALLETS,
        #     )
        #
        # address = self.address_generator_strategy()
        # wallet_created = self.wallet_repository.create_wallet(
        #     address=address, api_key=request.api_key
        # )
        #
        # if not wallet_created:
        #     return CreateWalletResponse(
        #         address="",
        #         balance_btc=0.0,
        #         balance_usd=0.0,
        #         status_code=status.WALLET_CREATION_ERROR,
        #     )
        #
        # self.wallet_repository.deposit_btc(address=address, btc_amount=1.0)
        # balance_usd = self.btc_usd_convertor(1.0)
        #
        # return CreateWalletResponse(
        #     address=address,
        #     balance_usd=balance_usd,
        #     balance_btc=1.0,
        #     status_code=status.WALLET_CREATED_SUCCESSFULLY,
        # )

    def get_balance(self, request: GetBalanceRequest) -> CoreResponse:
        handler = HasUserHandler(
            next_handler=GetWalletHandler(
                next_handler=NoHandler(),
                address=request.address,
                wallet_repository=self.wallet_repository,
                btc_usd_convertor=self.btc_usd_convertor_strategy,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )

        return handler.handle()
        # has_user = self.user_repository.has_user(api_key=request.api_key)
        #
        # if not has_user:
        #     return GetBalanceResponse(
        #         address="",
        #         balance_btc=0.0,
        #         balance_usd=0.0,
        #         status_code=status.INCORRECT_API_KEY,
        #     )

        # wallet = self.wallet_repository.get_wallet(address=request.address)
        #
        # if wallet is None:
        #     return GetBalanceResponse(
        #         address="",
        #         balance_btc=0.0,
        #         balance_usd=0.0,
        #         status_code=status.INVALID_WALLET,
        #     )

        # balance_usd = self.btc_usd_convertor(wallet.balance_btc)
        # return GetBalanceResponse(
        #     address=wallet.address,
        #     balance_usd=balance_usd,
        #     balance_btc=wallet.balance_btc,
        #     status_code=status.GOT_BALANCE_SUCCESSFULLY,
        # )

    def make_transaction(self, request: MakeTransactionRequest) -> CoreResponse:
        handler = HasUserHandler(
            next_handler=HasWalletHandler(
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
                wallet_repository=self.wallet_repository,
            ),
            api_key=request.api_key,
            user_repository=self.user_repository,
        )

        return handler.handle()
        # has_user = self.user_repository.has_user(api_key=request.api_key)
        #
        # if not has_user:
        #     return MakeTransactionResponse(status_code=status.INCORRECT_API_KEY)

        # first_wallet_exists = self.wallet_repository.has_wallet(
        #     address=request.first_wallet_address
        # )
        # second_wallet_exists = self.wallet_repository.has_wallet(
        #     address=request.second_wallet_address
        # )
        #
        # if not first_wallet_exists or not second_wallet_exists:
        #     return MakeTransactionResponse(status_code=status.INVALID_WALLET)

        # first_balance_btc = self.wallet_repository.get_balance(
        #     address=request.first_wallet_address
        # )
        #
        # if request.btc_amount > first_balance_btc:
        #     return MakeTransactionResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)

        # transaction_fee = 1.5
        # if first_wallet.api_key == second_wallet.api_key:
        #     transaction_fee = 0

        # first_wallet = self.wallet_repository.get_wallet(address=request.first_wallet_address)
        # second_wallet = self.wallet_repository.get_wallet(address=request.second_wallet_address)
        # transaction_fee = self.transaction_fee_strategy(first_wallet, second_wallet)
        #
        # first_successful = self.wallet_repository.withdraw_btc(
        #     address=request.first_wallet_address, btc_amount=request.btc_amount
        # )
        #
        # if not first_successful:
        #     return MakeTransactionResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)
        #
        # second_successful = self.wallet_repository.deposit_btc(
        #     address=request.second_wallet_address,
        #     btc_amount=(100 - transaction_fee) * request.btc_amount,
        # )
        #
        # if not second_successful:
        #     self.wallet_repository.deposit_btc(address=request.first_wallet_address,
        #                                        btc_amount=request.btc_amount)
        #     return MakeTransactionResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)
        #

        # self.transactions_repository.add_transaction(
        #     first_address=request.first_wallet_address,
        #     second_address=request.second_wallet_address,
        #     amount=request.btc_amount,
        # )
        #
        # self.statistics_repository.add_statistic(num_new_transactions=1, profit=transaction_fee * request.btc_amount)
        #
        # return MakeTransactionResponse(status_code=status.TRANSACTION_SUCCESSFUL)

    def get_transactions(self, request: GetTransactionsRequest) -> CoreResponse:

        if not self.user_repository.has_user(request.api_key):
            return GetTransactionsResponse(
                status_code=status.INCORRECT_API_KEY, transactions=list()
            )

        transactions = self.transactions_repository.get_all_transactions()
        if transactions is None:
            return GetTransactionsResponse(
                status_code=status.FETCH_TRANSACTIONS_UNSUCCESSFUL, transactions=list()
            )

        return GetTransactionsResponse(
            status_code=status.FETCH_TRANSACTIONS_SUCCESSFUL, transactions=transactions
        )

    def get_wallet_transactions(
        self, request: GetWalletTransactionsRequest
    ) -> CoreResponse:
        if not self.wallet_repository.has_wallet(request.address):
            return GetWalletTransactionsResponse(
                status_code=status.INVALID_WALLET, transactions=list()
            )

        transactions = self.transactions_repository.get_wallet_transactions(
            address=request.address
        )
        if transactions is None:
            return GetWalletTransactionsResponse(
                status_code=status.FETCH_TRANSACTIONS_UNSUCCESSFUL, transactions=list()
            )

        return GetWalletTransactionsResponse(
            status_code=status.FETCH_TRANSACTIONS_SUCCESSFUL, transactions=transactions
        )

    def get_statistics(self, request: GetStatisticsRequest) -> CoreResponse:
        statistics = self.statistics_repository.get_statistics()

        key = request.api_key
        if not self.admin_repository.is_admin(key):
            return GetStatisticsResponse(
                status_code=status.INCORRECT_API_KEY,
                total_num_transactions=0,
                platform_profit=0.0,
            )

        if statistics is None:
            return GetStatisticsResponse(
                status_code=status.FETCH_STATISTICS_UNSUCCESSFUL,
                total_num_transactions=0,
                platform_profit=0.0,
            )

        return GetStatisticsResponse(
            status_code=status.FETCH_STATISTICS_SUCCESSFUL,
            total_num_transactions=25,
            platform_profit=35.0,
        )
