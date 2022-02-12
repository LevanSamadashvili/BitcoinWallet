from dataclasses import dataclass
from sqlite3 import Connection, Cursor

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
    cursor: Cursor

    def create_user(self, api_key: str) -> bool:
        rows_modified = self.cursor.execute(
            "INSERT INTO users (api_key) VALUES (?)", (api_key,)
        ).rowcount
        self.connection.commit()
        return rows_modified > 0

    def has_user(self, api_key: str) -> bool:
        self.cursor.execute("SELECT * from users WHERE api_key = ?;", (api_key,))
        result_set = self.cursor.fetchall()
        return len(result_set) > 0
