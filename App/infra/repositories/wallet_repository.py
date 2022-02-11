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
