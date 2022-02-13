import sqlite3
import unittest
from sqlite3 import Connection, Cursor

from App.infra.repositories.user_repository import SQLiteUserRepository


class TestUserRepository(unittest.TestCase):
    connection: Connection
    cursor: Cursor
    user_repository: SQLiteUserRepository
    test_api_key: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.connection = sqlite3.connect("test_database.db", check_same_thread=False)
        cls.cursor = cls.connection.cursor()
        cls.user_repository = SQLiteUserRepository(connection=cls.connection)
        cls.user_repository.connection = cls.connection
        cls.test_api_key = "2"

    def setUp(self) -> None:
        self.cursor.execute("DELETE from users")

    def test_create_user(self) -> None:
        self.user_repository.create_user(api_key=self.test_api_key)
        self.cursor.execute(
            "SELECT * from users WHERE api_key = ?;", (self.test_api_key,)
        )
        result_set = self.cursor.fetchall()
        assert len(result_set) > 0

    def test_has_user_yes(self) -> None:
        self.cursor.execute(
            "INSERT INTO users (api_key) VALUES (?)", (self.test_api_key,)
        ).rowcount
        self.connection.commit()
        assert self.user_repository.has_user(self.test_api_key)

    def test_has_user_not(self) -> None:
        assert not self.user_repository.has_user(self.test_api_key)
