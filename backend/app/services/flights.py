"""Flight search service.

This module will integrate with flight data providers when available.
Currently returns structured mock data for development.
"""

from typing import List
from app.models.search import FlightResult


def search_flights(origin: str, destination: str, date: str, passengers: int) -> List[FlightResult]:
    """Search for flights between origin and destination.
    
    Args:
        origin: Departure city
        destination: Arrival city
        date: Departure date (YYYY-MM-DD)
        passengers: Number of passengers
    
    Returns:
        List of FlightResult objects
    """
    # Mock data for development
    # In production, this would call a flight search API
    return [
        FlightResult(
            id="flight-001",
            airline="Sample Airline A",
            departure_time="06:30",
            arrival_time="08:45",
            duration="2h 15m",
            stops=0,
            price=4800,
            currency="INR",
            booking_url=None,
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
    ]
