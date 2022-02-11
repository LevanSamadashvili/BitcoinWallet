from typing import Optional, Protocol

from App.core.models.statistics import Statistics


class IStatisticsRepository(Protocol):
    def get_statistics(self) -> Optional[Statistics]:
        pass
