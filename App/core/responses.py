from dataclasses import dataclass

from App.core.models.transaction import Transaction


@dataclass
class Response:
    status_code: int


@dataclass
class WalletParametersResponse:
    address: str
    balance_usd: float
    balance_btc: float


@dataclass
class RegisterUserResponse(Response):
    api_key: str


@dataclass
class CreateWalletResponse(Response, WalletParametersResponse):
    pass


@dataclass
class GetBalanceResponse(Response, WalletParametersResponse):
    pass


@dataclass
class GetTransactionsResponse(Response):
    transactions: list[Transaction]


@dataclass
class MakeTransactionResponse(Response):
    pass


@dataclass
class GetWalletTransactionsResponse(GetTransactionsResponse):
    transactions: list[Transaction]


@dataclass
class GetStatisticsResponse(Response):
    total_num_transactions: int
    platform_profit: float
