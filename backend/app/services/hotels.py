"""Hotel search service.

This module will integrate with hotel data providers when available.
Currently returns structured mock data for development.
"""

from typing import List
from app.models.search import HotelResult


def search_hotels(destination: str, check_in: str, check_out: str, guests: int) -> List[HotelResult]:
    """Search for hotels at destination.
    
    Args:
        destination: City or area
        check_in: Check-in date (YYYY-MM-DD)
        check_out: Check-out date (YYYY-MM-DD)
        guests: Number of guests
    
    Returns:
        List of HotelResult objects
    """
    # Mock data for development
    # In production, this would call a hotel search API
    return [
        HotelResult(
            id="hotel-001",
            name="Sample Hotel A",
            area="City centre",
            price_per_night=2200,
            currency="INR",
            booking_url=None,
        ),
        HotelResult(
            id="hotel-002",
            name="Sample Hotel B",
            area="Near the station",
            price_per_night=1500,
            currency="INR",
            booking_url=None,
        ),
    ]
