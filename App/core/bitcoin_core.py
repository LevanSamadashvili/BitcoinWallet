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
    RegisterUserResponse,
)


class BitcoinCore:
    def __init__(self) -> None:
        pass

    def register_user(self, request: RegisterUserRequest) -> RegisterUserResponse:
        pass

    def create_wallet(self, request: CreateWalletRequest) -> CreateWalletResponse:
        pass

    def get_balance(self, request: GetBalanceRequest) -> GetBalanceResponse:
        pass

    def make_transaction(
        self, request: MakeTransactionRequest
    ) -> MakeTransactionResponse:
        pass

    def get_transactions(
        self, request: GetTransactionsRequest
    ) -> GetTransactionsResponse:
        pass

    def get_wallet_transactions(
        self, request: GetWalletTransactionsRequest
    ) -> GetWalletTransactionsResponse:
        pass

    def get_statistics(self, request: GetStatisticsRequest) -> GetStatisticsResponse:
        pass
