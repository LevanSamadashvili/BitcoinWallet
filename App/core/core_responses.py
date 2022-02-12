from dataclasses import dataclass

from App.core.models.transaction import Transaction


@dataclass
class CoreResponse:
    status_code: int


@dataclass
class RegisterUserResponse(CoreResponse):
    api_key: str


@dataclass
class CreateWalletResponse(CoreResponse):
    address: str
    balance_usd: float
    balance_btc: float


@dataclass
class GetBalanceResponse(CoreResponse):
    address: str
    balance_usd: float
    balance_btc: float


@dataclass
class GetTransactionsResponse(CoreResponse):
    transactions: list[Transaction]


@dataclass
class MakeTransactionResponse(CoreResponse):
    pass


@dataclass
class SaveTransactionResponse(CoreResponse):
    pass


@dataclass
class GetWalletTransactionsResponse(GetTransactionsResponse):
    transactions: list[Transaction]


@dataclass
class GetStatisticsResponse(CoreResponse):
    total_num_transactions: int
    platform_profit: float
