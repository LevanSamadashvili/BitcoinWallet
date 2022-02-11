from typing import Optional, Protocol

from App.core.Models.Statistics import Statistics


class IStatisticsRepository(Protocol):
    def get_statistics(self) -> Optional[Statistics]:
        pass
