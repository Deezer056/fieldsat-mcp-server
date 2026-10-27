"""Tool: satellite and weather evidence for one field, fetched at the same time."""

import asyncio
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field

from fieldsat.domain.contracts import SatelliteContext, WeatherContext
from fieldsat.domain.errors import (
    SourceUnavailableError,
    field_not_registered_message,
    source_unavailable_message,
)
from fieldsat.domain.fields import FieldLookup
from fieldsat.domain.satellite import get_satellite_analysis as build_satellite_analysis
from fieldsat.domain.weather import get_weather_context as build_weather_context
from fieldsat.providers.base import SatelliteEvidenceProvider, WeatherEvidenceProvider
from fieldsat.tools.common import READ_ONLY, TOOL_TIMEOUT_SECONDS, FieldId


class FieldReport(BaseModel):
    field_id: str
    satellite: SatelliteContext | None
    weather: WeatherContext | None
    errors: list[str]


def register_summary_tools(
    mcp: FastMCP,
    satellite_provider: SatelliteEvidenceProvider,
    weather_provider: WeatherEvidenceProvider,
    find_field: FieldLookup,
) -> None:
    @mcp.tool(
        name="get_field_summary",
        title="Get field summary",
        annotations=READ_ONLY,
        timeout=TOOL_TIMEOUT_SECONDS,
    )
    async def get_field_summary(
        field_id: FieldId,
        comparison_days: Annotated[
            int,
            Field(
                ge=1,
                le=90,
                description="Length of each current and previous comparison period in days",
            ),
        ] = 14,
    ) -> FieldReport:
        """Satellite vegetation evidence and weather context for one field in a single call.

        Fetches both sources at the same time. If one source is unavailable, the other is
        still returned and `errors` says what is missing.
        """
        field = find_field(field_id)
        if field is None:
            raise ToolError(field_not_registered_message(field_id))
        # Both requests run concurrently; return_exceptions keeps one failure from
        # cancelling the other.
        satellite, weather = await asyncio.gather(
            build_satellite_analysis(field, comparison_days, satellite_provider),
            build_weather_context(field, 7, 2, weather_provider),
            return_exceptions=True,
        )
        errors: list[str] = []
        for result in (satellite, weather):
            if isinstance(result, SourceUnavailableError):
                errors.append(source_unavailable_message(result))
            elif isinstance(result, BaseException):
                raise result
        if len(errors) == 2:
            raise ToolError(" ".join(errors))
        return FieldReport(
            field_id=field.id,
            satellite=None if isinstance(satellite, BaseException) else satellite,
            weather=None if isinstance(weather, BaseException) else weather,
            errors=errors,
        )
