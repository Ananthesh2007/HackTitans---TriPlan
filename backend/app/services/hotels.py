"""Hotel search service.

This module will integrate with hotel data providers when available.
Currently returns structured mock data for development.

The check-in time and the concessions on each rate are what the filters on
the search page work on.
"""

from typing import List, Optional

from app.models.search import HotelResult, SearchFilters
from app.services.filters import apply_filters, sort_results

# The sample hotels.
HOTEL_SAMPLES: List[HotelResult] = [
    HotelResult(
        id="hotel-001",
        name="Sample Hotel A",
        area="City centre",
        price_per_night=2200,
        currency="INR",
        booking_url=None,
        check_in_time="14:00",
        concessions=["senior_citizen", "army", "student"],
    ),
    HotelResult(
        id="hotel-002",
        name="Sample Hotel B",
        area="Near the station",
        price_per_night=1500,
        currency="INR",
        booking_url=None,
        check_in_time="12:00",
        concessions=["senior_citizen", "army", "student", "doctor", "nurse"],
    ),
    HotelResult(
        id="hotel-003",
        name="Sample Hotel C",
        area="Quiet outskirts",
        price_per_night=3400,
        currency="INR",
        booking_url=None,
        check_in_time="15:00",
        concessions=["senior_citizen", "student"],
    ),
    HotelResult(
        id="hotel-004",
        name="Sample Hotel D",
        area="Near the beach",
        price_per_night=2800,
        currency="INR",
        booking_url=None,
        check_in_time="10:00",
        concessions=["senior_citizen", "army", "doctor"],
    ),
]


def search_hotels(
    destination: str,
    check_in: str,
    check_out: str,
    guests: int,
    concession: Optional[str] = None,
    filters: Optional[SearchFilters] = None,
) -> List[HotelResult]:
    """Search for hotels at destination.

    Args:
        destination: City or area
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        guests: Number of guests
        concession: The concession category the traveller books under, if any
        filters: The filters the search page picked

    Returns:
        List of HotelResult objects, filtered and sorted as asked.
    """
    # In production, this would call a hotel search API.
    results = apply_filters(HOTEL_SAMPLES, filters, concession)
    return sort_results(results, filters.sort if filters else "recommended")
