import sqlite3
import unittest

from App.infra.repositories.wallet_repository import SQLiteWalletRepository


class TestWalletRepository(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = sqlite3.connect("test_database.db")
        self.cursor = self.connection.cursor()
        self.wallet_repository = SQLiteWalletRepository(connection=self.connection)
        self.cursor.execute("DELETE FROM users")
        self.cursor.execute("DELETE FROM wallets")

    def tearDown(self) -> None:
        self.cursor.execute("DELETE FROM users")
        self.cursor.execute("DELETE FROM wallets")
        self.connection.close()

    def add_test_user(self) -> None:
        self.test_api_key = "test_api_key"
        self.cursor.execute("INSERT INTO users(api_key) VALUES (?)", (self.test_api_key,))

    def add_test_wallet(self) -> None:
        self.test_address = "test_add"
        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (self.test_address, self.test_api_key, 0),
        )

    def test_create_wallet(self) -> None:
        self.add_test_user()
        address = "test_add"
        self.wallet_repository.create_wallet(address=address, api_key=self.test_api_key)
        result_set = self.cursor.execute(
            "SELECT * from wallets WHERE api_key = ? AND address = ?;",
            (self.test_api_key, address),
        ).fetchall()
        assert len(result_set) == 1
        assert result_set[0][0] == address
        assert result_set[0][1] == self.test_api_key
        assert result_set[0][2] == 0

    def test_has_wallet(self) -> None:
        self.add_test_user()
        self.add_test_wallet()
        assert self.wallet_repository.has_wallet(self.test_address)
        assert self.wallet_repository.get_balance(self.test_address) == 0

    def test_get_balance(self) -> None:
        self.add_test_user()
        test_address = "test_add"
        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (test_address, self.test_api_key, 1.5),
        )
        assert self.wallet_repository.get_balance(test_address) == 1.5

    def test_deposit_btc(self) -> None:
        self.add_test_user()
        self.add_test_wallet()
        self.wallet_repository.deposit_btc(self.test_address, 50)
        test_balance = 50
        result_set = self.cursor.execute(
            "SELECT balance FROM wallets WHERE address = ?", (self.test_address,)
        ).fetchall()
        assert result_set[0][0] == test_balance

    def test_withdraw_btc(self) -> None:
        self.add_test_user()
        test_address = "test_add"
        test_balance = 50
        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (test_address, self.test_api_key, test_balance),
        )
        self.wallet_repository.withdraw_btc(test_address, 10)
        result_set = self.cursor.execute(
            "SELECT balance FROM wallets WHERE address = ?", (test_address,)
        ).fetchall()
        assert result_set[0][0] == test_balance - 10

    def test_get_wallet(self) -> None:
        self.add_test_user()
        test_address = "test_add"
        test_balance = 50
        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (test_address, self.test_api_key, test_balance),
        )
        test_wallet = self.wallet_repository.get_wallet(test_address)
        assert test_wallet is not None
        assert test_wallet.api_key == self.test_api_key
        assert test_wallet.address == test_address
        assert test_wallet.balance_btc == test_balance

    def test_get_wallet_none(self) -> None:
        self.cursor.execute("DELETE FROM wallets")
        test_address = "test"
        wallet = self.wallet_repository.get_wallet(test_address)
        assert wallet is None

    def test_num_wallets(self) -> None:
        self.add_test_user()
        test_address = "test_add"
        test_second_address = "test_add1"
        test_third_address = "test_add2"
        test_balance = 50
        test_second_balance = 10
        test_third_balance = 15.4

        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (test_address, self.test_api_key, test_balance),
        )
        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (test_second_address, self.test_api_key, test_second_balance),
        )
        self.cursor.execute(
            "INSERT INTO wallets(address, api_key, balance) VALUES (?, ?, ?)",
            (test_third_address, self.test_api_key, test_third_balance),
        )

        assert self.wallet_repository.get_num_wallets(self.test_api_key) == 3
