"""Map and route service.

Turns the place names in an itinerary into points on a map and works out a
practical visiting order.

Providers
---------
- Geocoding: OpenStreetMap Nominatim (no API key needed).
- Routing: OSRM (no API key needed).

Both providers are open and free for light use, so the default works out of
the box. Set `MAPS_PROVIDER=google` to use Google Maps instead, once
`MAPS_API_KEY` is set.

Rules for this file
-------------------
- The API key is read from the environment only (see `app/config.py`).
- Nothing is invented. When a place cannot be found, or the provider cannot
  be reached, the answer says so instead of guessing coordinates.
- Every failure mode returns a normal value; nothing here raises past the
  module, so a maps outage never breaks the trip page.
"""

import logging
import math
import threading
import time
from typing import Iterable

import httpx

from app import config
from app.models.maps import (
    Coordinates,
    DayMap,
    PlaceLocation,
    RouteLeg,
    RouteResult,
    RouteStop,
    TripMapResponse,
)

logger = logging.getLogger("triplan.maps")

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OSRM_URL = "https://router.project-osrm.org/route/v1/driving"
GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

# The earth radius in kilometres, used for the straight-line fallback.
EARTH_RADIUS_KM = 6371.0

# How many places we look up for one day of a trip.
MAX_STOPS_PER_DAY = 8

# How many points a route line keeps. A provider can answer with hundreds,
# and a long trip would make the response very large.
MAX_ROUTE_POINTS = 120

# Used when a provider gives no route data, so the frontend can still show
# the stops on a map and say the distance is an estimate.
AVERAGE_SPEED_KMH = 30.0

# Nominatim allows at most one request a second. We wait between calls
# instead of getting the whole IP blocked.
NOMINATIM_MIN_INTERVAL_SECONDS = 1.1

# How long a geocoding answer stays in the cache (seconds).
GEOCODE_CACHE_TTL_SECONDS = 24 * 60 * 60

# The geocode cache. A trip has many places, and the same place often shows
# up in more than one trip, so this saves a lot of requests.
_geocode_cache: dict[str, tuple[float, PlaceLocation | None]] = {}

# The route cache, keyed by the coordinates of the stops.
_route_cache: dict[str, tuple[float, RouteResult]] = {}

# Guards the cache and the request spacing.
_cache_lock = threading.Lock()
_last_nominatim_call = 0.0


class MapsError(Exception):
    """Raised when a maps provider cannot give us a usable answer."""


# ---------- Geocoding ----------


def _wait_for_nominatim_slot() -> None:
    """Keep at least a second between Nominatim calls.

    Their usage policy allows one request a second. We sleep only when a
    call was made very recently, so the first request is never delayed.
    """
    global _last_nominatim_call

    with _cache_lock:
        now = time.monotonic()
        wait_for = NOMINATIM_MIN_INTERVAL_SECONDS - (now - _last_nominatim_call)
        if wait_for > 0:
            time.sleep(wait_for)
        _last_nominatim_call = time.monotonic()


def _cache_key(place: str) -> str:
    return f"{config.MAPS_PROVIDER}:{place.strip().lower()}"


def _read_cache(place: str) -> PlaceLocation | None | bool:
    """Read a place from the cache.

    Returns the PlaceLocation, None for a cached "not found", or False when
    the place is not in the cache at all.
    """
    key = _cache_key(place)
    with _cache_lock:
        entry = _geocode_cache.get(key)
        if entry is None:
            return False
        stored_at, location = entry
        if time.monotonic() - stored_at > GEOCODE_CACHE_TTL_SECONDS:
            _geocode_cache.pop(key, None)
            return False
        return location


def _write_cache(place: str, location: PlaceLocation | None) -> None:
    """Store a place in the cache. A miss is cached too, so we do not ask
    the provider again for a place that does not exist."""
    with _cache_lock:
        _geocode_cache[_cache_key(place)] = (time.monotonic(), location)


def geocode_place(place: str) -> PlaceLocation | None:
    """Look up one place name and return where it is.

    Args:
        place: Name of the place, e.g. "Cubbon Park, Bengaluru".

    Returns:
        A PlaceLocation, or None when the place cannot be found or the
        provider is unavailable. None means "we do not know", never a guess.
    """
    place = (place or "").strip()
    if not place:
        return None

    if not config.is_maps_configured():
        return None

    cached = _read_cache(place)
    if cached is not False:
        return cached  # type: ignore[return-value]

    try:
        if config.MAPS_PROVIDER == "google":
            location = _geocode_google(place)
        else:
            _wait_for_nominatim_slot()
            location = _geocode_nominatim(place)
    except MapsError as exc:
        logger.warning("Geocoding failed for %r: %s", place, exc)
        return None
    except httpx.HTTPError as exc:
        logger.warning("Could not reach the geocoding provider: %s", exc)
        return None

    _write_cache(place, location)
    return location


def _geocode_nominatim(place: str) -> PlaceLocation | None:
    """Geocode with OpenStreetMap Nominatim."""
    params = {
        "q": place,
        "format": "jsonv2",
        "limit": 1,
        # Bias the search to the region the user is travelling in.
        "addressdetails": 0,
    }
    headers = {"User-Agent": config.MAPS_USER_AGENT}

    try:
        with httpx.Client(timeout=config.MAPS_TIMEOUT_SECONDS) as client:
            response = client.get(NOMINATIM_URL, params=params, headers=headers)
    except httpx.TimeoutException as exc:
        raise MapsError(f"The geocoding provider did not answer in time: {exc}") from exc
    except httpx.HTTPError as exc:
        raise MapsError(f"Could not reach the geocoding provider: {exc}") from exc

    if response.status_code >= 400:
        raise MapsError(f"The geocoding provider returned HTTP {response.status_code}.")

    try:
        results = response.json()
    except ValueError as exc:
        raise MapsError("The geocoding provider returned a response we could not read.") from exc

    if not isinstance(results, list) or not results:
        return None

    first = results[0]
    try:
        lat = float(first["lat"])
        lng = float(first["lon"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MapsError("The geocoding provider returned an unexpected shape.") from exc

    return PlaceLocation(
        query=place,
        name=first.get("name") or None,
        display_name=first.get("display_name") or None,
        coordinates=Coordinates(lat=lat, lng=lng),
        provider="osm",
    )


def _geocode_google(place: str) -> PlaceLocation | None:
    """Geocode with the Google Maps Geocoding API."""
    params = {"address": place, "key": config.MAPS_API_KEY}

    try:
        with httpx.Client(timeout=config.MAPS_TIMEOUT_SECONDS) as client:
            response = client.get(GOOGLE_GEOCODE_URL, params=params)
    except httpx.TimeoutException as exc:
        raise MapsError(f"The geocoding provider did not answer in time: {exc}") from exc
    except httpx.HTTPError as exc:
        raise MapsError(f"Could not reach the geocoding provider: {exc}") from exc

    if response.status_code >= 400:
        raise MapsError(f"The geocoding provider returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise MapsError("The geocoding provider returned a response we could not read.") from exc

    results = payload.get("results") or []
    if not results:
        return None

    location = results[0].get("geometry", {}).get("location", {})
    try:
        lat = float(location["lat"])
        lng = float(location["lng"])
    except (KeyError, TypeError, ValueError) as exc:
        raise MapsError("The geocoding provider returned an unexpected shape.") from exc

    return PlaceLocation(
        query=place,
        name=results[0].get("formatted_address") or None,
        display_name=results[0].get("formatted_address") or None,
        coordinates=Coordinates(lat=lat, lng=lng),
        provider="google",
    )


# ---------- Routing ----------


def build_route(stops: list[RouteStop], mode: str = "driving") -> RouteResult:
    """Work out the route that visits the stops in order.

    Args:
        stops: The stops of one day, in the order they should be visited.
        mode: Travel mode. Only "driving" is routed for now.

    Returns:
        A RouteResult. When the routing provider is unavailable the result
        carries `is_estimate=True` and a straight-line distance, so the
        frontend can show something and say clearly that it is an estimate.
    """
    if len(stops) < 2:
        return RouteResult(
            provider=config.MAPS_PROVIDER,
            mode=mode,
            is_estimate=False,
            warning="A route needs at least two stops.",
        )

    points = [stop.coordinates for stop in stops if stop.coordinates]
    if len(points) < 2:
        return RouteResult(
            provider=config.MAPS_PROVIDER,
            mode=mode,
            is_estimate=True,
            warning="Not every stop could be located, so the route is an estimate.",
        )

    if not config.is_maps_configured():
        return _estimated_route(stops, points, mode)

    cache_key = ";".join(f"{point.lat},{point.lng}" for point in points)
    cached = _read_route_cache(cache_key)
    if cached is not None:
        return cached

    try:
        result = _route_osrm(stops, points, mode)
    except MapsError as exc:
        logger.warning("Routing failed, using the estimated route: %s", exc)
        result = _estimated_route(stops, points, mode)
        result.warning = "Live route data is not available, so the route is an estimate."
        return result
    except httpx.HTTPError as exc:
        logger.warning("Could not reach the routing provider: %s", exc)
        result = _estimated_route(stops, points, mode)
        result.warning = "Live route data is not available, so the route is an estimate."
        return result

    _write_route_cache(cache_key, result)
    return result


def _thin_points(points: list[Coordinates], max_points: int = MAX_ROUTE_POINTS) -> list[Coordinates]:
    """Cut the number of points in a route line.

    A routing provider can answer with hundreds of points for one day. That
    is far more detail than a map on a phone needs, and a long trip would
    make the response very large. The first and the last point are always
    kept, so the line still starts and ends at the stops.
    """
    if len(points) <= max_points:
        return points

    step = len(points) / (max_points - 1)
    kept = [points[int(index * step)] for index in range(max_points - 1)]
    kept.append(points[-1])
    return kept


def _read_route_cache(key: str) -> RouteResult | None:
    with _cache_lock:
        entry = _route_cache.get(key)
        if entry is None:
            return None
        stored_at, result = entry
        if time.monotonic() - stored_at > GEOCODE_CACHE_TTL_SECONDS:
            _route_cache.pop(key, None)
            return None
        return result


def _write_route_cache(key: str, result: RouteResult) -> None:
    with _cache_lock:
        _route_cache[key] = (time.monotonic(), result)


def _route_osrm(stops: list[RouteStop], points: list[Coordinates], mode: str) -> RouteResult:
    """Get the route from OSRM."""
    coordinates = ";".join(f"{point.lng},{point.lat}" for point in points)
    url = f"{OSRM_URL}/{coordinates}"
    params = {"overview": "full", "geometries": "geojson", "steps": "false"}

    try:
        with httpx.Client(timeout=config.MAPS_TIMEOUT_SECONDS) as client:
            response = client.get(url, params=params)
    except httpx.TimeoutException as exc:
        raise MapsError(f"The routing provider did not answer in time: {exc}") from exc
    except httpx.HTTPError as exc:
        raise MapsError(f"Could not reach the routing provider: {exc}") from exc

    if response.status_code >= 400:
        raise MapsError(f"The routing provider returned HTTP {response.status_code}.")

    try:
        payload = response.json()
    except ValueError as exc:
        raise MapsError("The routing provider returned a response we could not read.") from exc

    if payload.get("code") != "Ok" or not payload.get("routes"):
        raise MapsError("The routing provider could not build a route for these stops.")

    route = payload["routes"][0]
    distance_km = float(route.get("distance", 0.0)) / 1000.0
    duration_minutes = float(route.get("duration", 0.0)) / 60.0

    geometry = (route.get("geometry") or {}).get("coordinates") or []
    route_points = [
        Coordinates(lat=pair[1], lng=pair[0])
        for pair in geometry
        if isinstance(pair, (list, tuple)) and len(pair) >= 2
    ]
    route_points = _thin_points(route_points)

    legs = []
    raw_legs = route.get("legs") or []
    for index in range(len(stops) - 1):
        raw_leg = raw_legs[index] if index < len(raw_legs) else {}
        legs.append(
            RouteLeg(
                from_stop=stops[index].name,
                to_stop=stops[index + 1].name,
                distance_km=round(float(raw_leg.get("distance", 0.0)) / 1000.0, 2),
                duration_minutes=round(float(raw_leg.get("duration", 0.0)) / 60.0, 1),
            )
        )

    return RouteResult(
        provider="osm",
        mode=mode,
        distance_km=round(distance_km, 2),
        duration_minutes=round(duration_minutes, 1),
        points=route_points,
        legs=legs,
        is_estimate=False,
    )


def _estimated_route(
    stops: list[RouteStop], points: list[Coordinates], mode: str
) -> RouteResult:
    """Build a straight-line route when no routing provider answered.

    The distance is the sum of the straight lines between the stops, and the
    duration uses a fixed average speed. Both are flagged as estimates.
    """
    total_km = 0.0
    for first, second in zip(points, points[1:]):
        total_km += haversine_km(first, second)

    duration_minutes = (total_km / AVERAGE_SPEED_KMH) * 60.0

    legs = []
    for index in range(len(stops) - 1):
        leg_km = haversine_km(points[index], points[index + 1])
        legs.append(
            RouteLeg(
                from_stop=stops[index].name,
                to_stop=stops[index + 1].name,
                distance_km=round(leg_km, 2),
                duration_minutes=round((leg_km / AVERAGE_SPEED_KMH) * 60.0, 1),
            )
        )

    return RouteResult(
        provider="estimate",
        mode=mode,
        distance_km=round(total_km, 2),
        duration_minutes=round(duration_minutes, 1),
        points=list(points),
        legs=legs,
        is_estimate=True,
        warning="Live route data is not available, so the route is an estimate.",
    )


def haversine_km(first: Coordinates, second: Coordinates) -> float:
    """Straight-line distance between two points, in kilometres."""
    lat1, lon1 = math.radians(first.lat), math.radians(first.lng)
    lat2, lon2 = math.radians(second.lat), math.radians(second.lng)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------- Map links ----------


def map_url_for(latitude: float, longitude: float, label: str | None = None) -> str:
    """A link that opens the point in a map on the user's device."""
    query = f"?q={latitude},{longitude}"
    if label:
        query += f"({label})"
    return f"https://www.openstreetmap.org/{query}"


# ---------- The service the routes call ----------


def build_trip_map(trip) -> TripMapResponse:
    """Build the map of every day of a trip.

    Each activity of a day becomes a stop. The stops are geocoded, and the
    route between them is worked out. Days whose places cannot be found
    still appear, with a warning, so the frontend can say which part of the
    plan could not be located.

    Args:
        trip: The Trip with its itinerary.

    Returns:
        A TripMapResponse. `is_mock` is True when no provider answered.
    """
    response = TripMapResponse(
        trip_id=trip.trip_id,
        destination=trip.destination,
        provider=config.MAPS_PROVIDER if config.is_maps_configured() else None,
    )

    if not config.is_maps_configured():
        response.is_mock = True
        response.warning = "The map service is not configured."
        return response

    located_any = False

    for day in trip.itinerary:
        day_map = DayMap(day=day.day, title=day.title)

        stops: list[RouteStop] = []
        activities = list(day.activities)[:MAX_STOPS_PER_DAY]

        for index, activity in enumerate(activities):
            location = geocode_place(activity.location)
            if location is None:
                stops.append(
                    RouteStop(
                        order=index + 1,
                        name=activity.name,
                        location=activity.location,
                        coordinates=None,
                    )
                )
                continue

            located_any = True
            stops.append(
                RouteStop(
                    order=index + 1,
                    name=activity.name,
                    location=activity.location,
                    coordinates=location.coordinates,
                    map_url=map_url_for(
                        location.coordinates.lat,
                        location.coordinates.lng,
                        activity.name,
                    ),
                )
            )

        day_map.stops = stops

        missing = [stop for stop in stops if stop.coordinates is None]
        if missing:
            day_map.warning = (
                f"{len(missing)} of {len(stops)} places could not be located on the map."
            )

        day_map.route = build_route(stops)
        response.days.append(day_map)

    if not located_any:
        response.is_mock = True
        response.warning = "None of the places in this plan could be located."

    return response


def suggest_visit_order(stops: Iterable[RouteStop]) -> list[RouteStop]:
    """Order stops so nearby places are visited together.

    This is a simple nearest-neighbour order starting from the first stop.
    It uses straight-line distances, so it is a suggestion, not a claim
    about the fastest real route.
    """
    remaining = list(stops)
    if len(remaining) < 3:
        return remaining

    located = [stop for stop in remaining if stop.coordinates is not None]
    if len(located) < 3:
        return remaining

    ordered = [located[0]]
    pool = located[1:]

    while pool:
        current = ordered[-1].coordinates
        closest = min(
            pool,
            key=lambda stop: haversine_km(current, stop.coordinates),
        )
        pool.remove(closest)
        ordered.append(closest)

    return ordered
