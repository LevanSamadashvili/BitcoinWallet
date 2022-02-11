from App.core.Models.user import User
from App.core.repository_interfaces.user_repository import IUserRepository


class InMemoryUserRepository(IUserRepository):
    users: set[User] = set()

    def create_user(self, api_key: str) -> bool:
        if self.has_user(api_key=api_key):
            return False
        self.users.add(User(api_key=api_key))
        return True

    def has_user(self, api_key: str) -> bool:
        user = User(api_key=api_key)
        return user in self.users
