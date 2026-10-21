"""Shapes used by the map and route service.

The models follow the same rules as the rest of the API (see
docs/api-contract.md):

- Nothing is invented. A place that cannot be located has no coordinates
  (`coordinates` stays `null`) instead of a made-up point.
- Every distance and duration is either taken from a routing provider or
  clearly flagged as an estimate (`is_estimate`).
"""

from pydantic import BaseModel, Field

from app.models.common import Place


class Coordinates(BaseModel):
    """A point on the map."""

    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class PlaceLocation(BaseModel):
    """A place name resolved to a point on the map."""

    query: str
    name: str | None = None
    display_name: str | None = None
    coordinates: Coordinates
    provider: str


class GeocodeRequest(BaseModel):
    """POST /api/maps/geocode"""

    place: Place


class RouteStop(BaseModel):
    """One stop of a route, in visiting order."""

    order: int
    name: str
    location: str
    coordinates: Coordinates | None = None
    map_url: str | None = None


class RouteLeg(BaseModel):
    """The travel between two consecutive stops."""

    from_stop: str
    to_stop: str
    distance_km: float | None = Field(default=None, ge=0)
    duration_minutes: float | None = Field(default=None, ge=0)


class RouteResult(BaseModel):
    """The route between the stops of one day."""

    provider: str
    mode: str
    distance_km: float | None = Field(default=None, ge=0)
    duration_minutes: float | None = Field(default=None, ge=0)
    # The line to draw on the map. Empty when the provider gave no geometry.
    points: list[Coordinates] = Field(default_factory=list)
    legs: list[RouteLeg] = Field(default_factory=list)
    # True when the figures are a straight-line calculation, not route data.
    is_estimate: bool = False
    warning: str | None = None


class DayMap(BaseModel):
    """The map of one day of a trip."""

    day: int
    title: str
    stops: list[RouteStop] = Field(default_factory=list)
    route: RouteResult | None = None
    warning: str | None = None


class TripMapResponse(BaseModel):
    """GET /api/trips/{trip_id}/map"""

    trip_id: str
    destination: str
    provider: str | None = None
    days: list[DayMap] = Field(default_factory=list)
    # True when no provider answered, so the map is empty.
    is_mock: bool = False
    warning: str | None = None
