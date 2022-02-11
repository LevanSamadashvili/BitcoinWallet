from typing import Optional

from App.core.Models.transaction import Transaction
from App.core.repository_interfaces.transactions_repository import (
    ITransactionsRepository,
)


class InMemoryTransactionsRepository(ITransactionsRepository):
    transactions: list[Transaction]

    def add_transaction(
        self, first_address: str, second_address: str, amount: float
    ) -> bool:
        self.transactions.append(
            Transaction(
                first_address=first_address,
                second_address=second_address,
                amount=amount,
            )
        )
        return True

    def get_all_transactions(self) -> Optional[list[Transaction]]:
        return self.transactions

    def get_wallet_transactions(self, address: str) -> Optional[list[Transaction]]:
        result: list[Transaction] = list()
        for transaction in self.transactions:
            if (
                transaction.first_address == address
                or transaction.second_address == address
            ):
                result.append(transaction)
        return result
