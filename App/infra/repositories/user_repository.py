from dataclasses import dataclass
from sqlite3 import Connection

from App.core.models.user import User
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


@dataclass
class SQLiteUserRepository(IUserRepository):
    connection: Connection

    def __init__(self, connection: Connection):
        self.connection = connection

    def create_user(self, api_key: str) -> bool:
        cursor = self.connection.cursor()
        rows_modified = cursor.execute(
            "INSERT INTO users (api_key) VALUES (?)", (api_key,)
        ).rowcount
        self.connection.commit()
        if rows_modified > 0:
            return True
        return False

    def has_user(self, api_key: str) -> bool:
        cursor = self.connection.cursor()
        cursor.execute("SELECT * from users WHERE api_key = ?;", (api_key,))
        result_set = cursor.fetchall()
        return len(result_set) > 0
