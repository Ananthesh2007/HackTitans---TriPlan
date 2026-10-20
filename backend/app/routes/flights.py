from fastapi import APIRouter

from app.errors import AppError
from app.models.search import FlightSearchRequest, FlightSearchResponse, FlightResult

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
def search_flights(payload: FlightSearchRequest):
    """Search for flights. Currently returns mock data."""
    try:
        # Generate mock flight results
        results = [
            FlightResult(
                id="flight-001",
                airline="Sample Airline A",
                departure_time="06:30",
                arrival_time="08:45",
                duration="2h 15m",
                stops=0,
                price=4800,
                currency="INR",
                booking_url=None,  # No verified provider integrated yet
            ),
            FlightResult(
                id="flight-002",
                airline="Sample Airline B",
                departure_time="11:10",
                arrival_time="14:50",
                duration="3h 40m",
                stops=1,
                price=3900,
                currency="INR",
                booking_url=None,
            ),
            FlightResult(
                id="flight-003",
                airline="Sample Airline C",
                departure_time="18:20",
                arrival_time="20:35",
                duration="2h 15m",
                stops=0,
                price=5600,
                currency="INR",
                booking_url=None,
            ),
        ]

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
        "message": "Complete your booking on the external provider's website."
    }# 19-10-2026 — URL validation: verified allowlists in flights.py/hotels.py
