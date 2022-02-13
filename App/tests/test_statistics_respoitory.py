import sqlite3
import unittest
from sqlite3 import Connection, Cursor

from App.infra.repositories.statistics_repository import SQLiteStatisticsRepository


class TestStatisticsRepository(unittest.TestCase):
    connection: Connection
    cursor: Cursor
    statistics_repository: SQLiteStatisticsRepository
    test_api_key: str

    @classmethod
    def setUpClass(cls) -> None:
        cls.connection = sqlite3.connect("test_database.db", check_same_thread=False)
        cls.cursor = cls.connection.cursor()
        cls.statistics_repository = SQLiteStatisticsRepository(
            connection=cls.connection
        )
        cls.test_api_key = "2"

    def setUp(self) -> None:
        self.cursor.execute("DELETE from statistics")

    def test_add_statistics_one(self) -> None:
        self.statistics_repository.add_statistic(5, 5.0)
        result_set = self.cursor.execute("SELECT * FROM statistics").fetchall()
        self.statistics_repository.add_statistic(2, 2.0)
        assert len(result_set) == 1

    def test_add_statistics_none(self) -> None:
        result_set = self.cursor.execute("SELECT * FROM statistics").fetchall()
        assert len(result_set) == 0

    def get_statistics(self) -> None:
        self.cursor.execute(
            "INSERT INTO statistics (num_transactions, profit) VALUES (?, ?)",
            (3, 10.0),
        )
        self.connection.commit()
        self.cursor.execute(
            "UPDATE statistics SET num_transactions = ?, profit = ?",
            (5, 15.0),
        )
        self.connection.commit()
        result_stat = self.statistics_repository.get_statistics()
        assert result_stat is not None
        assert result_stat.profit == 15.0
        assert result_stat.num_transactions == 5
