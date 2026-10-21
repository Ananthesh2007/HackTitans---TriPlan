"""Bus and train search service.

This module will integrate with transport data providers when available.
Currently returns structured mock data for development.

The AC type, the seat class, the live tracking flag and the concessions on
each fare are what the filters on the search page work on.
"""

from typing import List, Optional

from app.models.search import SearchFilters, TransportResult
from app.services.filters import apply_filters, sort_results

# The sample trains.
TRAIN_SAMPLES: List[TransportResult] = [
    TransportResult(
        id="train-001",
        operator="Sample Express 1",
        vehicle_type="Sleeper class",
        departure_time="20:10",
        arrival_time="06:00",
        duration="9h 50m",
        price=480,
        currency="INR",
        booking_url=None,
        tracking=True,
        is_new=False,
        concessions=["senior_citizen", "student", "army"],
    ),
    TransportResult(
        id="train-002",
        operator="Sample Express 2",
        vehicle_type="AC 3 tier",
        departure_time="22:40",
        arrival_time="07:20",
        duration="8h 40m",
        price=1250,
        currency="INR",
        booking_url=None,
        tracking=True,
        is_new=True,
        concessions=["senior_citizen", "student", "army", "doctor", "nurse"],
    ),
    TransportResult(
        id="train-003",
        operator="Sample Passenger 3",
        vehicle_type="Second sitting",
        departure_time="05:30",
        arrival_time="15:10",
        duration="9h 40m",
        price=190,
        currency="INR",
        booking_url=None,
        tracking=False,
        is_new=False,
        concessions=["senior_citizen", "student"],
    ),
]

# The sample buses.
BUS_SAMPLES: List[TransportResult] = [
    TransportResult(
        id="bus-001",
        operator="Sample Bus Operator A",
        vehicle_type="AC sleeper",
        departure_time="21:30",
        arrival_time="05:15",
        duration="7h 45m",
        price=900,
        currency="INR",
        booking_url=None,
        tracking=True,
        is_new=True,
        concessions=["senior_citizen", "student", "army"],
    ),
    TransportResult(
        id="bus-002",
        operator="Sample Bus Operator B",
        vehicle_type="Non-AC seater",
        departure_time="22:00",
        arrival_time="06:30",
        duration="8h 30m",
        price=550,
        currency="INR",
        booking_url=None,
        tracking=False,
        is_new=False,
        concessions=["senior_citizen", "student"],
    ),
    TransportResult(
        id="bus-003",
        operator="Sample Bus Operator C",
        vehicle_type="AC seater",
        departure_time="23:15",
        arrival_time="06:45",
        duration="7h 30m",
        price=750,
        currency="INR",
        booking_url=None,
        tracking=True,
        is_new=False,
        concessions=["senior_citizen", "army", "doctor", "nurse"],
    ),
    TransportResult(
        id="bus-004",
        operator="Sample Bus Operator D",
        vehicle_type="Non-AC sleeper",
        departure_time="19:45",
        arrival_time="04:20",
        duration="8h 35m",
        price=420,
        currency="INR",
        booking_url=None,
        tracking=False,
        is_new=True,
        concessions=["senior_citizen", "student", "army"],
    ),
]


def search_transport(
    mode: str,
    origin: str,
    destination: str,
    date: str,
    passengers: int,
    concession: Optional[str] = None,
    filters: Optional[SearchFilters] = None,
) -> List[TransportResult]:
    """Search for buses or trains.

    Args:
        mode: "bus" or "train"
        origin: Departure city
        destination: Arrival city
        date: Travel date (YYYY-MM-DD)
        passengers: Number of passengers
        concession: The concession category the traveller books under, if any
        filters: The filters the search page picked

    Returns:
        List of TransportResult objects, filtered and sorted as asked.
    """
    # In production, this would call a transport search API.
    samples = TRAIN_SAMPLES if mode == "train" else BUS_SAMPLES
    results = apply_filters(samples, filters, concession)
    return sort_results(results, filters.sort if filters else "recommended")
