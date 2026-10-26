"""Weather aggregation for the frozen seven-day and 48-hour output windows."""

from collections import defaultdict
from collections.abc import Iterable
from datetime import date, timedelta

from fieldsat.domain.contracts import WeatherContext
from fieldsat.domain.evidence import WeatherHour
from fieldsat.domain.fields import RegisteredField
from fieldsat.providers.base import WeatherEvidenceProvider

HEAVY_RAIN_48_HOURS_MM = 30.0
HEAVY_RAIN_7_DAYS_MM = 75.0


def _sum_rainfall(hours: Iterable[WeatherHour]) -> float:
    return sum(hour.rainfall_mm for hour in hours)


def _average_humidity(hours: Iterable[WeatherHour]) -> float | None:
    values = [
        hour.relative_humidity_percentage
        for hour in hours
        if hour.relative_humidity_percentage is not None
    ]
    return sum(values) / len(values) if values else None


async def get_weather_context(
    field: RegisteredField,
    historical_days: int,
    forecast_days: int,
    provider: WeatherEvidenceProvider,
) -> WeatherContext:
    if historical_days < 1:
        raise ValueError("historical_days must be a positive integer.")
    if forecast_days < 1:
        raise ValueError("forecast_days must be a positive integer.")

    evidence = await provider.get_daily_context(
        field, max(7, historical_days), max(3, forecast_days)
    )
    if evidence.as_of.tzinfo is None:
        raise ValueError("Weather evidence as_of must be timezone-aware.")
    if any(hour.timestamp.tzinfo is None for hour in (*evidence.history, *evidence.forecast)):
        raise ValueError("Weather evidence timestamps must be timezone-aware.")

    first_local_date = evidence.as_of.date() - timedelta(days=6)
    last_7_days = tuple(
        hour
        for hour in evidence.history
        if first_local_date <= hour.timestamp.date() <= evidence.as_of.date()
        and hour.timestamp <= evidence.as_of
    )
    last_48_hours = tuple(
        hour
        for hour in evidence.history
        if evidence.as_of - timedelta(hours=48) < hour.timestamp <= evidence.as_of
    )
    next_48_hours = tuple(
        hour
        for hour in evidence.forecast
        if evidence.as_of < hour.timestamp <= evidence.as_of + timedelta(hours=48)
    )

    daily_rainfall: dict[date, float] = defaultdict(float)
    for hour in last_7_days:
        daily_rainfall[hour.timestamp.date()] += hour.rainfall_mm

    rainfall_last_7_days = _sum_rainfall(last_7_days)
    rainfall_last_48_hours = _sum_rainfall(last_48_hours)
    rainfall_next_48_hours = _sum_rainfall(next_48_hours)
    average_humidity = _average_humidity(last_7_days)

    return WeatherContext(
        rainfall_last_7_days_mm=round(rainfall_last_7_days, 1),
        rainy_days_last_7_days=sum(rainfall > 0 for rainfall in daily_rainfall.values()),
        rainfall_last_48_hours_mm=round(rainfall_last_48_hours, 1),
        rainfall_forecast_next_48_hours_mm=round(rainfall_next_48_hours, 1),
        average_humidity_last_7_days=(
            round(average_humidity, 1) if average_humidity is not None else None
        ),
        heavy_rain_recent=(
            rainfall_last_48_hours >= HEAVY_RAIN_48_HOURS_MM
            or rainfall_last_7_days >= HEAVY_RAIN_7_DAYS_MM
        ),
        heavy_rain_expected=rainfall_next_48_hours >= HEAVY_RAIN_48_HOURS_MM,
    )
