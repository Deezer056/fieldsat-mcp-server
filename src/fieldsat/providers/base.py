"""Async provider contracts implemented by live services and test doubles."""

from typing import Protocol

from ..domain.evidence import SatelliteEvidence, WeatherEvidence
from ..domain.fields import RegisteredField


class SatelliteEvidenceProvider(Protocol):
    async def get_period_summary(
        self, field: RegisteredField, comparison_days: int
    ) -> SatelliteEvidence: ...


class WeatherEvidenceProvider(Protocol):
    async def get_daily_context(
        self, field: RegisteredField, historical_days: int, forecast_days: int
    ) -> WeatherEvidence: ...
