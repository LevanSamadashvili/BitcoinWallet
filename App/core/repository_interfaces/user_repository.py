from typing import Protocol


class IUserRepository(Protocol):
    def create_user(self, api_key: str) -> bool:
        pass

    def has_user(self, api_key: str) -> bool:
        pass

    def is_admin(self, api_key: str) -> bool:
        pass
