"""Flight search service.

This module will integrate with flight data providers when available.
Currently returns structured mock data for development.

The concessions on each fare are what the concession filter on the search
page works on.
"""

import datetime
from typing import List, Optional

from app.models.search import FlightResult, SearchFilters
from app.services.filters import apply_filters, sort_results

# The sample flights with realistic carrier names and direct booking URLs.
FLIGHT_SAMPLES: List[FlightResult] = [
    FlightResult(
        id="flight-001",
        airline="Air India Express",
        departure_time="06:30",
        arrival_time="08:45",
        duration="2h 15m",
        stops=0,
        price=4800,
        currency="INR",
        booking_url="https://www.airindiaexpress.com",
        source_name="Amadeus GDS",
        last_checked_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        concessions=["senior_citizen", "student", "army"],
    ),
    FlightResult(
        id="flight-002",
        airline="IndiGo",
        departure_time="11:10",
        arrival_time="14:50",
        duration="3h 40m",
        stops=1,
        price=3900,
        currency="INR",
        booking_url="https://www.goindigo.in",
        source_name="Amadeus GDS",
        last_checked_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        concessions=["senior_citizen", "student", "army", "doctor", "nurse"],
    ),
    FlightResult(
        id="flight-003",
        airline="Akasa Air",
        departure_time="18:20",
        arrival_time="20:35",
        duration="2h 15m",
        stops=0,
        price=5600,
        currency="INR",
        booking_url="https://www.akasaair.com",
        source_name="Amadeus GDS",
        last_checked_timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        concessions=["senior_citizen", "student"],
    ),
]


def search_flights(
    origin: str,
    destination: str,
    date: str,
    passengers: int,
    concession: Optional[str] = None,
    filters: Optional[SearchFilters] = None,
) -> List[FlightResult]:
    """Search for flights between origin and destination.

    Args:
        origin: Departure city
        destination: Arrival city
        date: Departure date (YYYY-MM-DD)
        passengers: Number of passengers
        concession: The concession category the traveller books under, if any
        filters: The filters the search page picked

    Returns:
        List of FlightResult objects, filtered and sorted as asked.
    """
    # In production, this would call a flight search API.
    results = apply_filters(FLIGHT_SAMPLES, filters, concession)
    return sort_results(results, filters.sort if filters else "recommended")
