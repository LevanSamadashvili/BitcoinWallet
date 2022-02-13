from dataclasses import dataclass

from App.core.models.transaction import Transaction


@dataclass
class ResponseContent:
    pass

@dataclass
class RegisterUserResponse(ResponseContent):
    api_key: str


@dataclass
class CreateWalletResponse(ResponseContent):
    address: str
    balance_usd: float
    balance_btc: float


@dataclass
class GetBalanceResponse(ResponseContent):
    address: str
    balance_usd: float
    balance_btc: float


@dataclass
class GetTransactionsResponse(ResponseContent):
    transactions: list[Transaction]


@dataclass
class MakeTransactionResponse(ResponseContent):
    pass


@dataclass
class SaveTransactionResponse(ResponseContent):
    pass


@dataclass
class GetWalletTransactionsResponse(GetTransactionsResponse):
    transactions: list[Transaction]


@dataclass
class GetStatisticsResponse(ResponseContent):
    total_num_transactions: int
    platform_profit: float


@dataclass
class CoreResponse:
    status_code: int = 0
    response_content: ResponseContent = ResponseContent()
