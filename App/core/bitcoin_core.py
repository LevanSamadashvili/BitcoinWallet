from dataclasses import dataclass
from typing import Callable, Union

from App.core import status
from App.core.repository_interfaces.statistics_repository import IStatisticsRepository
from App.core.repository_interfaces.transactions_repository import (
    ITransactionsRepository,
)
from App.core.repository_interfaces.user_repository import IUserRepository
from App.core.repository_interfaces.wallet_repository import IWalletRepository
from App.core.requests import (
    CreateWalletRequest,
    GetBalanceRequest,
    GetStatisticsRequest,
    GetTransactionsRequest,
    GetWalletTransactionsRequest,
    MakeTransactionRequest,
    RegisterUserRequest,
)
from App.core.responses import (
    CreateWalletResponse,
    GetBalanceResponse,
    GetStatisticsResponse,
    GetTransactionsResponse,
    GetWalletTransactionsResponse,
    MakeTransactionResponse,
    RegisterUserResponse, Response,
)

MAX_AVAILABLE_WALLETS = 3


def default_api_key_generator() -> str:
    return "1"


def default_address_generator() -> str:
    return "1"


def default_btc_usd_convertor(btc_amount: float) -> float:
    return 2 * btc_amount


@dataclass
class BitcoinCore:
    user_repository: IUserRepository
    wallet_repository: IWalletRepository
    transactions_repository: ITransactionsRepository
    statistics_repository: IStatisticsRepository

    api_key_generator_strategy: Callable[[], str]
    address_generator_strategy: Callable[[], str]
    btc_usd_convertor: Callable[[float], float]

    def register_user(self, request: RegisterUserRequest) -> RegisterUserResponse:
        api_key = self.api_key_generator_strategy()
        user_created = self.user_repository.create_user(api_key)

        if not user_created:
            return RegisterUserResponse(
                status_code=status.USER_REGISTRATION_ERROR, api_key=""
            )

        return RegisterUserResponse(
            status_code=status.USER_CREATED_SUCCESSFULLY, api_key=api_key
        )

    def create_wallet(self, request: CreateWalletRequest) -> Union[CreateWalletResponse, Response]:
        has_user = self.user_repository.has_user(api_key=request.api_key)

        if not has_user:
            return CreateWalletResponse(
                address="",
                balance_btc=0.0,
                balance_usd=0.0,
                status_code=status.INCORRECT_API_KEY,
            )


        num_wallets = self.wallet_repository.get_num_wallets(api_key=request.api_key)

        if num_wallets == MAX_AVAILABLE_WALLETS:
            return CreateWalletResponse(
                address="",
                balance_btc=0.0,
                balance_usd=0.0,
                status_code=status.CANT_CREATE_MORE_WALLETS,
            )

        address = self.address_generator_strategy()
        wallet_created = self.wallet_repository.create_wallet(
            address=address, api_key=request.api_key
        )

        if not wallet_created:
            return CreateWalletResponse(
                address="",
                balance_btc=0.0,
                balance_usd=0.0,
                status_code=status.WALLET_CREATION_ERROR,
            )

        self.wallet_repository.deposit_btc(address=address, btc_amount=1.0)
        balance_usd = self.btc_usd_convertor(1.0)

        return CreateWalletResponse(
            address=address,
            balance_usd=balance_usd,
            balance_btc=1.0,
            status_code=status.WALLET_CREATED_SUCCESSFULLY,
        )

    def get_balance(self, request: GetBalanceRequest) -> GetBalanceResponse:
        has_user = self.user_repository.has_user(api_key=request.api_key)

        if not has_user:
            return GetBalanceResponse(
                address="",
                balance_btc=0.0,
                balance_usd=0.0,
                status_code=status.INCORRECT_API_KEY,
            )

        wallet = self.wallet_repository.get_wallet(address=request.address)
        balance_usd = self.btc_usd_convertor(wallet.balance_btc)
        return GetBalanceResponse(
            address=wallet.address,
            balance_usd=balance_usd,
            balance_btc=wallet.balance_btc,
            status_code=status.GOT_BALANCE_SUCCESSFULLY,
        )

    def make_transaction(
        self, request: MakeTransactionRequest
    ) -> MakeTransactionResponse:
        has_user = self.user_repository.has_user(api_key=request.api_key)

        if not has_user:
            return MakeTransactionResponse(status_code=status.TRANSACTION_SUCCESSFUL)

        first_balance_btc = self.wallet_repository.get_balance(address=request.first_wallet_address)

        if request.btc_amount > first_balance_btc:
            return MakeTransactionResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)

        first_wallet = self.wallet_repository.get_wallet(address=request.first_wallet_address)
        second_wallet = self.wallet_repository.get_wallet(address=request.second_wallet_address)

        self.wallet_repository.withdraw_btc(address=request.first_wallet_address, btc_amount=request.btc_amount)
        self.wallet_repository.deposit_btc(address=request.second_wallet_address, btc_amount=request.btc_amount)



    def get_transactions(
        self, request: GetTransactionsRequest
    ) -> GetTransactionsResponse:
        return GetTransactionsResponse(status_code=200)

    def get_wallet_transactions(
        self, request: GetWalletTransactionsRequest
    ) -> GetWalletTransactionsResponse:
        return GetWalletTransactionsResponse(status_code=200)

    def get_statistics(self, request: GetStatisticsRequest) -> GetStatisticsResponse:
        return GetStatisticsResponse(
            status_code=200, total_num_transactions=25, platform_profit=35.0
        )
