from App.core.Models.user import User
from App.core.repository_interfaces.admin_repository import IAdminRepository


class InMemoryAdminRepository(IAdminRepository):
    admins: list[User] = list()

    def __init__(self, api_key: str):
        self.admins.append(User(api_key=api_key))

    def add_admin(self, api_key: str) -> bool:
        self.admins.append(User(api_key=api_key))
        return True

    def is_admin(self, api_key: str) -> bool:
        user = User(api_key=api_key)
        return user in self.admins
