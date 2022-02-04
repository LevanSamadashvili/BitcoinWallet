from dataclasses import dataclass


@dataclass
class RegisterUserRequest:
    first_name: str
    last_name: str


@dataclass
class ApiKeyRequest:
    api_key: str


@dataclass
class CreateWalletRequest(ApiKeyRequest):
    pass


@dataclass
class GetBalanceRequest(ApiKeyRequest):
    address: str


@dataclass
class GetTransactionsRequest(ApiKeyRequest):
    pass


@dataclass
class MakeTransactionRequest(ApiKeyRequest):
    first_wallet_address: str
    second_wallet_address: str
    btc_amount: float


@dataclass
class GetWalletTransactionsRequest(ApiKeyRequest):
    address: str


@dataclass
class GetStatisticsRequest(ApiKeyRequest):
    pass
