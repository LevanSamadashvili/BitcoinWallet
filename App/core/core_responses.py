from dataclasses import dataclass

from App.core import status
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
    message: str = ""
    status_code: int = status.DEFAULT_STATUS_CODE
    response_content: ResponseContent = ResponseContent()
