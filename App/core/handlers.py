from dataclasses import dataclass
from typing import Callable, Protocol

from App.core import status
from App.core.core_requests import AddressRequest, ApiKeyRequest, AmountAddressRequest
from App.core.core_responses import (
    CoreResponse,
    CreateWalletResponse,
    GetBalanceResponse, RegisterUserResponse, MakeTransactionResponse,
)
from App.core.models.wallet import Wallet
from App.core.observer import IObserver, StatisticsObserver, IObservable
from App.core.repository_interfaces.statistics_repository import IStatisticsRepository
from App.core.repository_interfaces.transactions_repository import ITransactionsRepository
from App.core.repository_interfaces.user_repository import IUserRepository
from App.core.repository_interfaces.wallet_repository import IWalletRepository

MAX_AVAILABLE_WALLETS = 3
INITIAL_BITCOINS_WALLET = 1.0


class IHandle(Protocol):
    def handle(self) -> CoreResponse:
        pass


@dataclass
class CreateUserHandler(IHandle):
    next_handler: IHandle
    user_repository: IUserRepository
    api_key_generator_strategy: Callable[[], str]

    def handle(self) -> CoreResponse:
        api_key = self.api_key_generator_strategy()
        user_created = self.user_repository.create_user(api_key)

        if not user_created:
            return CoreResponse(status_code=status.USER_REGISTRATION_ERROR)

        return RegisterUserResponse(status_code=status.USER_CREATED_SUCCESSFULLY, api_key=api_key)


@dataclass
class HasUserHandler(IHandle):
    next_handler: IHandle
    api_key: str
    user_repository: IUserRepository

    def handle(self) -> CoreResponse:
        has_user = self.user_repository.has_user(api_key=self.api_key)

        if not has_user:
            return CoreResponse(status_code=status.INCORRECT_API_KEY)

        return self.next_handler.handle()


@dataclass
class MaxWalletsHandler(IHandle):
    next_handler: IHandle
    api_key: str
    wallet_repository: IWalletRepository

    def handle(self) -> CoreResponse:
        num_wallets = self.wallet_repository.get_num_wallets(
            api_key=self.api_key
        )

        if num_wallets == MAX_AVAILABLE_WALLETS:
            return CoreResponse(status_code=status.CANT_CREATE_MORE_WALLETS)

        return self.next_handler.handle()


@dataclass
class CreateWalletHandler(IHandle):
    next_handler: IHandle
    api_key: str
    wallet_repository: IWalletRepository
    address_generator_strategy: Callable[[], str]
    btc_usd_convertor: Callable[[float], float]

    def handle(self) -> CoreResponse:
        address = self.address_generator_strategy()
        wallet_created = self.wallet_repository.create_wallet(
            address=address, api_key=self.api_key
        )

        if not wallet_created:
            return CoreResponse(status_code=status.WALLET_CREATION_ERROR)

        self.wallet_repository.deposit_btc(
            address=address, btc_amount=INITIAL_BITCOINS_WALLET
        )
        balance_usd = self.btc_usd_convertor(INITIAL_BITCOINS_WALLET)

        return CreateWalletResponse(
            address=address,
            balance_usd=balance_usd,
            balance_btc=INITIAL_BITCOINS_WALLET,
            status_code=status.WALLET_CREATED_SUCCESSFULLY,
        )


@dataclass
class GetWalletHandler(IHandle):
    next_handler: IHandle
    address: str
    wallet_repository: IWalletRepository
    btc_usd_convertor: Callable[[float], float]

    def handle(self) -> CoreResponse:
        wallet = self.wallet_repository.get_wallet(address=self.address)

        if wallet is None:
            return CoreResponse(status_code=status.INVALID_WALLET)

        balance_usd = self.btc_usd_convertor(wallet.balance_btc)
        return GetBalanceResponse(
            address=wallet.address,
            balance_usd=balance_usd,
            balance_btc=wallet.balance_btc,
            status_code=status.GOT_BALANCE_SUCCESSFULLY,
        )


@dataclass
class TransactionValidationHandler(IHandle):
    next_handler: IHandle
    address: str
    btc_amount: float
    wallet_repository: IWalletRepository

    def handle(self) -> CoreResponse:
        balance_btc = self.wallet_repository.get_balance(
            address=self.address
        )

        if balance_btc < self.btc_amount:
            return CoreResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)

        return self.next_handler.handle()


@dataclass
class HasWalletHandler(IHandle):
    next_handler: IHandle
    address: str
    wallet_repository: IWalletRepository

    def handle(self) -> CoreResponse:
        wallet_exists = self.wallet_repository.has_wallet(address=self.address)

        if not wallet_exists:
            return CoreResponse(status_code=status.INVALID_WALLET)

        return self.next_handler.handle()

@dataclass
class MakeTransactionHandler(IHandle):
    next_handler: IHandle
    first_wallet_address: str
    second_wallet_address: str
    btc_amount: float
    wallet_repository: IWalletRepository
    transaction_fee_strategy: Callable[[Wallet, Wallet], float]

    def handle(self) -> CoreResponse:
        first_wallet = self.wallet_repository.get_wallet(address=self.first_wallet_address)
        second_wallet = self.wallet_repository.get_wallet(address=self.second_wallet_address)
        transaction_fee = self.transaction_fee_strategy(first_wallet, second_wallet)

        first_successful = self.wallet_repository.withdraw_btc(
            address=self.first_wallet_address, btc_amount=self.btc_amount
        )

        if not first_successful:
            return CoreResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)

        second_successful = self.wallet_repository.deposit_btc(
            address=self.second_wallet_address,
            btc_amount=(100 - transaction_fee) * self.btc_amount,
        )

        if not second_successful:
            self.wallet_repository.deposit_btc(address=self.first_wallet_address,
                                               btc_amount=self.btc_amount)
            return CoreResponse(status_code=status.TRANSACTION_UNSUCCESSFUL)

        return self.next_handler.handle()


@dataclass
class SaveTransactionHandler(IHandle):
    next_handler: IHandle
    first_address: str
    second_address: str
    btc_amount: float
    wallet_repository: IWalletRepository
    transactions_repository: ITransactionsRepository
    statistics_repository: IStatisticsRepository
    statistics_observer: StatisticsObserver
    transaction_fee_strategy: Callable[[Wallet, Wallet], float]

    def handle(self) -> CoreResponse:
        first_wallet = self.wallet_repository.get_wallet(address=self.first_address)

        if first_wallet is None:
            return CoreResponse(status_code=0)

        second_wallet = self.wallet_repository.get_wallet(address=self.second_address)

        if second_wallet is None:
            return CoreResponse(status_code=0)

        transaction_fee = self.transaction_fee_strategy(first_wallet, second_wallet)

        self.transactions_repository.add_transaction(
            first_address=self.first_address,
            second_address=self.second_address,
            amount=self.btc_amount,
        )

        self.statistics_observer.update(transaction_fee=transaction_fee, btc_amount=self.btc_amount, statistics_repository=self.statistics_repository)
        return MakeTransactionResponse(status_code=status.TRANSACTION_SUCCESSFUL)




class NoHandler(IHandle):
    def handle(self) -> CoreResponse:
        return CoreResponse(status_code=0)
