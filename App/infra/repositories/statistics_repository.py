from dataclasses import dataclass
from sqlite3 import Connection, Cursor
from typing import Optional

from App.core.models.statistics import Statistics
from App.core.repository_interfaces.statistics_repository import IStatisticsRepository


class InMemoryStatisticsRepository(IStatisticsRepository):
    statistics: Statistics = Statistics(num_transactions=0, profit=0.0)

    def get_statistics(self) -> Optional[Statistics]:
        return self.statistics

    def add_statistic(self, num_new_transactions: int, profit: float) -> None:
        self.statistics.num_transactions += num_new_transactions
        self.statistics.profit += profit


@dataclass
class SQLiteStatisticsRepository(IStatisticsRepository):
    connection: Connection
    cursor: Cursor

    def get_statistics(self) -> Optional[Statistics]:
        for (num_transactions, profit) in self.cursor.execute(
            "SELECT * FROM statistics"
        ):
            return Statistics(num_transactions=num_transactions, profit=profit)
        return None

    def add_statistic(self, num_new_transactions: int, profit: float) -> None:
        current_statistics = self.get_statistics()
        if current_statistics is None:
            self.cursor.execute(
                "INSERT INTO statistics (num_transactions, profit) VALUES (?, ?)",
                 (num_new_transactions, profit),
            )
            self.connection.commit()
            return
        updated_num_transactions = (
            current_statistics.num_transactions + num_new_transactions
        )
        updated_profit = current_statistics.profit + profit
        self.cursor.execute(
            "UPDATE statistics SET num_transactions = ?, profit = ?",
            (updated_num_transactions, updated_profit),
        )
        self.connection.commit()
