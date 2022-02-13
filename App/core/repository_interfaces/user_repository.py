from typing import Protocol


class IUserRepository:
    def create_user(self, api_key: str) -> bool:
        pass

    def has_user(self, api_key: str) -> bool:
        pass

