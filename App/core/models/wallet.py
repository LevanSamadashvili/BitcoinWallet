from dataclasses import dataclass


@dataclass
class Wallet:
    api_key: str
    address: str
    balance_btc: float

    def __hash__(self) -> int:
        return hash(self.address)
