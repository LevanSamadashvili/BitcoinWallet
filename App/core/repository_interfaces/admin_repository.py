from typing import Protocol, Optional


class IAdminRepository(Protocol):

    def add_admin(self, api_key: str) -> bool:
        pass

    def is_admin(self, api_key: str) -> bool:
        pass

