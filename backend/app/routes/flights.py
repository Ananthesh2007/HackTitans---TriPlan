from fastapi import APIRouter

from app.errors import AppError
from app.models.search import FlightSearchRequest, FlightSearchResponse
from app.services.flights import search_flights

router = APIRouter(prefix="/api/flights", tags=["flights"])

# Verified booking URLs allowlist
VERIFIED_AIRLINES = {
    "skyscanner": "https://www.skyscanner.co.in/",
    "makemytrip": "https://www.makemytrip.com/",
    "goibibo": "https://www.goibibo.com/",
    "cleartrip": "https://www.cleartrip.com/",
}


def validate_booking_url(url: str) -> bool:
    """Check if URL is from a verified booking provider."""
    if not url:
        return True  # None/empty is OK

    url_lower = url.lower()
    if not url_lower.startswith("https://"):
        return False

    return any(url_lower.startswith(allowed) for allowed in VERIFIED_AIRLINES.values())


@router.post("/search", response_model=FlightSearchResponse)
def search_flights_results(payload: FlightSearchRequest):
    """Search for flights. Currently returns mock data."""
    try:
        results = search_flights(
            origin=payload.origin,
            destination=payload.destination,
            date=payload.date.isoformat(),
            passengers=payload.passengers,
            concession=payload.concession,
            filters=payload.filters,
        )

        return FlightSearchResponse(is_mock=True, results=results)
    except Exception as e:
        raise AppError(500, "flight_search_failed", str(e))


@router.post("/booking-link")
def get_flight_booking_link(data: dict):
    """Get a verified booking link for a flight."""
    flight_id = data.get("flight_id")
    if not flight_id:
        raise AppError(400, "invalid_input", "flight_id is required.")

    # Return a verified external provider link
    # In production, this would integrate with an actual booking API
    booking_url = VERIFIED_AIRLINES["makemytrip"]

    return {
        "flight_id": flight_id,
        "booking_url": booking_url,
        "message": "Complete your booking on the external provider's website.",
    }# 19-10-2026 — URL validation: verified allowlists in flights.py/hotels.py
