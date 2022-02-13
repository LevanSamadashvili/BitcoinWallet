import sqlite3
import unittest
from sqlite3 import Connection, Cursor

from App.infra.repositories.transactions_repository import SQLiteTransactionsRepository


class TestTransactionsRepository(unittest.TestCase):
    connection: Connection
    cursor: Cursor
    transactions_repository: SQLiteTransactionsRepository
    first_address: str
    second_address: str
    amount: float
    first_api_key: str
    second_api_key: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.connection = sqlite3.connect("test_database.db", check_same_thread=False)
        cls.cursor = cls.connection.cursor()
        cls.transactions_repository = SQLiteTransactionsRepository(connection=sqlite3.connect("test_database.db", check_same_thread=False))
        cls.cursor = cls.transactions_repository.connection.cursor()
        cls.first_address = "111"
        cls.second_address = "222"
        cls.first_api_key = "1"
        cls.second_api_key = "2"
        cls.amount = 1.23

    def setUp(self) -> None:
        self.cursor.execute("DELETE from transactions")
        self.cursor.execute("DELETE from wallets")
        self.cursor.execute("DELETE from users")
        self.cursor.execute(
            "INSERT INTO users (api_key) VALUES (?)", (self.first_api_key,)
        ).rowcount
        self.connection.commit()
        self.cursor.execute(
            "INSERT INTO users (api_key) VALUES (?)", (self.second_api_key,)
        ).rowcount
        self.connection.commit()
        self.cursor.execute(
            "INSERT INTO wallets (address, api_key, balance) VALUES (?, ?, ?)",
            (self.first_address, self.first_api_key, 10),
        ).rowcount
        self.connection.commit()
        self.cursor.execute(
            "INSERT INTO wallets (address, api_key, balance) VALUES (?, ?, ?)",
            (self.second_address, self.second_api_key, 10),
        ).rowcount
        self.connection.commit()

    def test_add_transactions_accepted(self) -> None:
        self.transactions_repository.add_transaction(self.first_address, self.second_address, 5.0)
        result_set = self.cursor.execute("SELECT * FROM transactions WHERE first_address = ? AND second_address = ?",
                            (self.first_address, self.second_address)).fetchall()
        assert len(result_set) > 0
        address1, address2, amount = result_set[0]
        assert amount == 5.0

    def test_add_transactions_failed(self) -> None:
        self.transactions_repository.add_transaction(self.first_address, self.second_address, 5.0)
        result_set = self.cursor.execute("SELECT * FROM transactions WHERE first_address = ? AND second_address = ?",
                            (self.first_address, "333")).fetchall()
        assert len(result_set) == 0

    def test_get_all_transactions(self) -> None:
        self.transactions_repository.add_transaction(self.first_address, self.second_address, 5.0)
        self.transactions_repository.add_transaction(self.second_address, self.first_address, 2.0)
        result_set = self.transactions_repository.get_all_transactions()
        assert result_set is not None
        assert len(result_set) == 2

    def test_get_all_transactions_none(self) -> None:
        result_set = self.transactions_repository.get_all_transactions()
        assert result_set is not None
        assert len(result_set) == 0

    def test_get_wallet_transactions(self) -> None:
        self.transactions_repository.add_transaction(self.first_address, self.second_address, 5.0)
        self.transactions_repository.add_transaction(self.second_address, self.first_address, 2.0)
        self.cursor.execute(
            "INSERT INTO wallets (address, api_key, balance) VALUES (?, ?, ?)",
            ("NNN", self.second_api_key, 10),
        ).rowcount
        self.connection.commit()
        self.transactions_repository.add_transaction(self.second_address, "NNN", 10.0)
        result_set = self.transactions_repository.get_wallet_transactions(self.first_address)
        assert result_set is not None
        assert len(result_set) == 2

    def test_get_wallet_transaction_none(self) -> None:
        self.transactions_repository.add_transaction(self.second_address, "NNN", 10.0)
        result_set = self.transactions_repository.get_wallet_transactions(self.first_address)
        assert result_set is not None
        assert len(result_set) == 0











