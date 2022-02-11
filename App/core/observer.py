from App.core.repository_interfaces.statistics_repository import IStatisticsRepository


class StatisticsObserver:
    def update(
        self,
        transaction_fee: float,
        btc_amount: float,
        statistics_repository: IStatisticsRepository,
    ) -> None:
        statistics_repository.add_statistic(
            num_new_transactions=1, profit=transaction_fee * btc_amount
        )
