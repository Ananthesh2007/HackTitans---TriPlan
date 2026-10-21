"""Map endpoints for the TriPlan API.

- `GET /api/maps/geocode?place=Coorg` — find a place on the map.

The map of a whole trip lives in `app/routes/trips.py`, next to the other
trip endpoints, as `GET /api/trips/{trip_id}/map`.

Nothing here invents a location. When a place cannot be found, or the maps
provider is not configured, the answer says so instead of returning made-up
coordinates.
"""

from typing import Annotated

from fastapi import APIRouter, Query

from app import config
from app.models.common import Place
from app.services.maps import geocode_place

router = APIRouter(prefix="/api/maps", tags=["maps"])


@router.get("/geocode")
def geocode(place: Annotated[Place, Query(...)]):
    """Look up a place name and return where it is.

    Args:
        place: Name of the place, e.g. "Cubbon Park, Bengaluru".

    Returns:
        The place with its coordinates, or an error body when the place
        cannot be found or the map service is not configured.
    """
    if not config.is_maps_configured():
        return {
            "place": place,
            "error": "Map service not configured.",
        }

    location = geocode_place(place)
    if location is None:
        return {
            "place": place,
            "error": "This place could not be found on the map.",
        }

    return {
        "place": place,
        "name": location.name,
        "display_name": location.display_name,
        "coordinates": location.coordinates.model_dump(),
        "provider": location.provider,
        "map_url": (
            f"https://www.openstreetmap.org/?q={location.coordinates.lat},"
            f"{location.coordinates.lng}"
        ),
    }
