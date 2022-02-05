from typing import Optional

from App.core.Models.Statistics import Statistics
from App.core.repository_interfaces.statistics_repository import IStatisticsRepository


class InMemoryStatisticsRepository(IStatisticsRepository):
    statistics: Statistics = Statistics(num_transactions=0, profit=0.0)

    def get_statistics(self) -> Optional[Statistics]:
        return self.statistics
