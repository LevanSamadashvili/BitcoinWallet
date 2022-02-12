from dataclasses import dataclass
from sqlite3 import Connection, Cursor
from typing import Optional

from App.core.models.transaction import Transaction
from App.core.repository_interfaces.transactions_repository import (
    ITransactionsRepository,
)


class InMemoryTransactionsRepository(ITransactionsRepository):
    transactions: list[Transaction] = list()

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


@dataclass
class SQLiteTransactionsRepository(ITransactionsRepository):
    connection: Connection
    cursor: Cursor

    def add_transaction(
        self, first_address: str, second_address: str, amount: float
    ) -> bool:
        rows_modified = self.cursor.execute(
            "INSERT INTO transactions (first_address, second_address, amount) VALUES (?, ?, ?)",
            (first_address, second_address, amount),
        ).rowcount
        self.connection.commit()
        return rows_modified > 0

    def get_all_transactions(self) -> Optional[list[Transaction]]:
        result_set = []
        for (first_address, second_address, amount) in self.cursor.execute(
            "SELECT * FROM transactions"
        ):
            result_set.append(
                Transaction(
                    first_address=first_address,
                    second_address=second_address,
                    amount=amount,
                )
            )
        return result_set

    def get_wallet_transactions(self, address: str) -> Optional[list[Transaction]]:
        result_set = []
        for (first_address, second_address, amount) in self.cursor.execute(
            "SELECT * FROM transactions WHERE first_address = ? OR second_address = ?",
            (address, address),
        ):
            result_set.append(
                Transaction(
                    first_address=first_address,
                    second_address=second_address,
                    amount=amount,
                )
            )
        return result_set
