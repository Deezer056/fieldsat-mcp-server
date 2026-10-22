"""Choose where evidence comes from: live providers (needs credentials) or demo fixtures."""

from collections.abc import Mapping

from fastmcp import FastMCP

from .providers.copernicus import CopernicusCredentials, CopernicusSatelliteProvider
from .providers.fixtures import (
    DEMO_FIELDS,
    FIXTURE_SATELLITE_PROVIDER,
    FIXTURE_WEATHER_PROVIDER,
    find_demo_field,
)
from .providers.open_meteo import OpenMeteoWeatherProvider
from .server import create_server


def create_live_server(environment: Mapping[str, str] | None = None) -> FastMCP:
    """Copernicus Sentinel-2 and Open-Meteo. Refuses to start without Copernicus credentials."""
    credentials = CopernicusCredentials.from_environment(environment)
    return create_server(CopernicusSatelliteProvider(credentials), OpenMeteoWeatherProvider())


def create_demo_server() -> FastMCP:
    """Fixed numbers, no network, plus verification fields that fail on purpose."""
    return create_server(
        FIXTURE_SATELLITE_PROVIDER,
        FIXTURE_WEATHER_PROVIDER,
        fields=DEMO_FIELDS,
        find_field=find_demo_field,
    )
