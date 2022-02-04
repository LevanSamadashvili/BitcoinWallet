from dataclasses import dataclass


@dataclass
class Wallet:
    api_key: str
    address: str
    balance_btc: float
