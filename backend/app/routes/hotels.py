from fastapi import APIRouter

from app.errors import AppError
from app.models.search import HotelSearchRequest, HotelSearchResponse, HotelResult

router = APIRouter(prefix="/api/hotels", tags=["hotels"])

# Verified hotel booking URLs allowlist
VERIFIED_HOTEL_PROVIDERS = {
    "booking": "https://www.booking.com/",
    "makemytrip": "https://www.makemytrip.com/",
    "goibibo": "https://www.goibibo.com/",
    "agoda": "https://www.agoda.com/",
}


def validate_booking_url(url: str) -> bool:
    """Check if URL is from a verified hotel booking provider."""
    if not url:
        return True  # None/empty is OK

    url_lower = url.lower()
    if not url_lower.startswith("https://"):
        return False

    return any(url_lower.startswith(allowed) for allowed in VERIFIED_HOTEL_PROVIDERS.values())


@router.post("/search", response_model=HotelSearchResponse)
def search_hotels(payload: HotelSearchRequest):
    """Search for hotels. Currently returns mock data."""
    try:
        # Generate mock hotel results
        results = [
            HotelResult(
                id="hotel-001",
                name="Sample Hotel A",
                area="City centre",
                price_per_night=2200,
                currency="INR",
                booking_url=None,  # No verified provider integrated yet
            ),
            HotelResult(
                id="hotel-002",
                name="Sample Hotel B",
                area="Near the station",
                price_per_night=1500,
                currency="INR",
                booking_url=None,
            ),
            HotelResult(
                id="hotel-003",
                name="Sample Hotel C",
                area="Quiet outskirts",
                price_per_night=3400,
                currency="INR",
                booking_url=None,
            ),
        ]

        return HotelSearchResponse(is_mock=True, results=results)
    except Exception as e:
        raise AppError(500, "hotel_search_failed", str(e))


@router.post("/booking-link")
def get_hotel_booking_link(data: dict):
    """Get a verified booking link for a hotel."""
    hotel_id = data.get("hotel_id")
    if not hotel_id:
        raise AppError(400, "invalid_input", "hotel_id is required.")

    # Return a verified external provider link
    # In production, this would integrate with an actual booking API
    booking_url = VERIFIED_HOTEL_PROVIDERS["booking"]

    return {
        "hotel_id": hotel_id,
        "booking_url": booking_url,
        "message": "Complete your booking on the external provider's website."
    }