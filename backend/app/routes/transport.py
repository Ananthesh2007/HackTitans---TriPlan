from fastapi import APIRouter

from app.errors import AppError
from app.models.search import TransportSearchRequest, TransportSearchResponse, TransportResult

router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.post("/search", response_model=TransportSearchResponse)
def search_transport(payload: TransportSearchRequest):
    """Search for buses or trains. Currently returns mock data."""
    try:
        if payload.mode == "train":
            results = [
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
                ),
            ]
        else:  # bus
            results = [
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
                ),
            ]

        return TransportSearchResponse(is_mock=True, results=results)
    except Exception as e:
        raise AppError(500, "transport_search_failed", str(e))