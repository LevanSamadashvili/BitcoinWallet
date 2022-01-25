from dataclasses import dataclass


@dataclass
class RegisterUserResponse:
    api_key: str
    status_code: int


@dataclass
class CreateWalletResponse:
    address: str
    balance_usd: float
    balance_btc: float
    status_code: int
