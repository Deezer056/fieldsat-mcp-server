"""Weather aggregation tests."""

import pytest

from fieldsat.domain.fields import RegisteredField, find_registered_field
from fieldsat.domain.weather import get_weather_context
from fieldsat.providers.fixtures import FIXTURE_WEATHER_PROVIDER


def field(field_id: str) -> RegisteredField:
    result = find_registered_field(field_id)
    if result is None:
        raise AssertionError(f"Missing test field {field_id}")
    return result


@pytest.mark.asyncio
async def test_canonical_recent_and_forecast_rainfall() -> None:
    result = await get_weather_context(field("SL-PADDY-MINNERIYA"), 7, 2, FIXTURE_WEATHER_PROVIDER)
    assert result.model_dump() == {
        "rainfall_last_7_days_mm": 112.0,
        "rainy_days_last_7_days": 5,
        "rainfall_last_48_hours_mm": 38.0,
        "rainfall_forecast_next_48_hours_mm": 46.0,
        "average_humidity_last_7_days": 88.0,
        "heavy_rain_recent": True,
        "heavy_rain_expected": True,
    }


@pytest.mark.asyncio
async def test_output_windows_stay_fixed_for_any_valid_request() -> None:
    narrow = await get_weather_context(field("SL-PADDY-MINNERIYA"), 1, 1, FIXTURE_WEATHER_PROVIDER)
    wide = await get_weather_context(field("SL-PADDY-MINNERIYA"), 30, 7, FIXTURE_WEATHER_PROVIDER)
    assert narrow == wide
