from dataclasses import dataclass
from sqlite3 import Connection, Cursor
from typing import Optional

from App.core.models.wallet import Wallet
from App.core.repository_interfaces.wallet_repository import IWalletRepository


class InMemoryWalletRepository(IWalletRepository):
    wallets: dict[str, Wallet] = dict()

    def create_wallet(self, address: str, api_key: str) -> bool:
        self.wallets[address] = Wallet(
            address=address, api_key=api_key, balance_btc=0.0
        )
        return True

    def has_wallet(self, address: str) -> bool:
        return address in self.wallets

    def deposit_btc(self, address: str, btc_amount: float) -> bool:
        wallet = self.wallets[address]
        wallet.balance_btc += btc_amount
        return True

    def withdraw_btc(self, address: str, btc_amount: float) -> bool:
        wallet = self.wallets[address]
        wallet.balance_btc -= btc_amount
        return True

    def get_balance(self, address: str) -> float:
        return self.wallets[address].balance_btc

    def get_num_wallets(self, api_key: str) -> int:
        count = 0
        for address, wallet in self.wallets.items():
            if wallet.api_key == api_key:
                count += 1
        return count

    def get_wallet(self, address: str) -> Optional[Wallet]:
        return self.wallets[address]


@dataclass
class SQLiteWalletRepository(IWalletRepository):
    connection: Connection
    cursor: Cursor

    def create_wallet(self, address: str, api_key: str) -> bool:
        rows_modified = self.cursor.execute(
            "INSERT INTO wallets (address, api_key, balance) VALUES (?, ?, ?)",
            (address, api_key, 0),
        ).rowcount
        self.connection.commit()
        return rows_modified > 0

    def has_wallet(self, address: str) -> bool:
        self.cursor.execute("SELECT * from wallets WHERE address = ?;", (address,))
        result_set = self.cursor.fetchall()
        return len(result_set) > 0

    def deposit_btc(self, address: str, btc_amount: float) -> bool:
        current_balance = self.get_balance(address)
        updated_balance = current_balance + btc_amount
        self.cursor.execute(
            "UPDATE wallets SET balance = ? WHERE address = ? ",
            (updated_balance, address),
        )
        self.connection.commit()
        if self.get_balance(address) == updated_balance:
            return True
        return False

    def withdraw_btc(self, address: str, btc_amount: float) -> bool:
        return self.deposit_btc(address, -btc_amount)

    def get_balance(self, address: str) -> float:
        self.cursor.execute(
            "SELECT balance from wallets WHERE address = ?;", (address,)
        )
        result_set = self.cursor.fetchall()
        return float(result_set[0][0])

    def get_num_wallets(self, api_key: str) -> int:
        self.cursor.execute(
            "SELECT count(*) from wallets WHERE api_key = ?;", (api_key,)
        )
        result_set = self.cursor.fetchall()
        return int(result_set[0][0])

    def get_wallet(self, address: str) -> Optional[Wallet]:
        if not self.has_wallet(address):
            return None
        self.cursor.execute("SELECT * from wallets WHERE address = ?;", (address,))
        result_set = self.cursor.fetchall()
        if len(result_set) <= 0:
            return None
        wallet = result_set[0]
        return Wallet(api_key=wallet[1], address=wallet[0], balance_btc=wallet[2])
