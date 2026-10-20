"""Weather endpoint for the TriPlan API.

The shape follows docs/api-contract.md exactly:

- `GET /api/weather?place=Coorg&date=2026-11-20`

No live weather provider is wired up yet, so the endpoint always answers
with the contract's "provider not available" body. It never invents weather
data for a real place.
"""
import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from pydantic import AfterValidator

from app.models.common import Place, not_in_past

router = APIRouter(prefix="/api/weather", tags=["weather"])

# The date must be today or later. The validator turns a past date into a
# normal 422 validation error instead of a server error.
#
# Note: Query() has to sit inside the Annotated, not be used as the default.
# As a default it replaces the whole annotation and the validator is dropped.
TripDate = Annotated[datetime.date, AfterValidator(not_in_past), Query(...)]

# Same reason: StringConstraints is only applied when it stays in the annotation.
WeatherPlace = Annotated[Place, Query(...)]

# Date and place are echoed back, so they are required query parameters.
_Echoed = Annotated[str, Query(...)]


@router.get("", response_model=dict)
@router.get("/", response_model=dict)
def get_weather(place: WeatherPlace, date: TripDate):
    """Get weather information for a place and date.

    Args:
        place: Name of the place to get weather for.
        date: Date of the trip. Must be today or later.

    Returns:
        The contract's "provider not available" body, because no live
        weather provider is configured yet.
    """
    # A real implementation would call a weather API (e.g. OpenWeatherMap)
    # here and return condition, temperature_min, temperature_max, humidity
    # and description. Until then we say so instead of inventing data.
    return {
        "place": place,
        "date": date.isoformat(),
        "error": "Weather service not configured.",
    }
