from dataclasses import dataclass


@dataclass
class RegisterUserRequest:
    pass


@dataclass
class ApiKeyRequest:
    api_key: str


@dataclass
class AddressRequest:
    address: str


@dataclass
class BtcAmountRequest:
    btc_amount: float


@dataclass
class AmountAddressRequest(AddressRequest, BtcAmountRequest):
    pass


@dataclass
class CreateWalletRequest(ApiKeyRequest):
    pass


@dataclass
class GetBalanceRequest(ApiKeyRequest, AddressRequest):
    pass


@dataclass
class GetTransactionsRequest(ApiKeyRequest):
    pass


@dataclass
class MakeTransactionRequest(ApiKeyRequest, BtcAmountRequest):
    first_wallet_address: str
    second_wallet_address: str


@dataclass
class GetWalletTransactionsRequest(ApiKeyRequest, AddressRequest):
    pass


@dataclass
class GetStatisticsRequest(ApiKeyRequest):
    pass
