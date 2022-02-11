from typing import Optional, Protocol

from App.core.Models.wallet import Wallet


class IWalletRepository(Protocol):
    def create_wallet(self, address: str, api_key: str) -> bool:
        pass

    def has_wallet(self, address: str) -> bool:
        pass

    def deposit_btc(self, address: str, btc_amount: float) -> bool:
        pass

    def withdraw_btc(self, address: str, btc_amount: float) -> bool:
        pass

    def get_balance(self, address: str) -> float:
        pass

    def get_num_wallets(self, api_key: str) -> int:
        pass

    def get_wallet(self, address: str) -> Optional[Wallet]:
        pass
