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
