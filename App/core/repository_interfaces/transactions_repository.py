from typing import Protocol, Optional

from App.core.Models.transaction import Transaction


class ITransactionsRepository(Protocol):
    def add_transaction(self, first_address: str, second_address: str, amount: float) -> bool:
        pass

    def get_all_transactions(self) -> Optional[list[Transaction]]:
        pass

    def get_wallet_transactions(self, address: str) -> Optional[list[Transaction]]:
        pass
