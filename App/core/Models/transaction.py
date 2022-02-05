from dataclasses import dataclass


@dataclass
class Transaction:
    first_address: str
    second_address: str
    amount: float