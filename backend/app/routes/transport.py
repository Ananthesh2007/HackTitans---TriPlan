from fastapi import APIRouter

from app.errors import AppError
from app.models.search import TransportSearchRequest, TransportSearchResponse
from app.services.transport import search_transport

router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.post("/search", response_model=TransportSearchResponse)
def search_transport_results(payload: TransportSearchRequest):
    """Search for buses or trains. Currently returns mock data."""
    try:
        results = search_transport(
            mode=payload.mode,
            origin=payload.origin,
            destination=payload.destination,
            date=payload.date.isoformat(),
            passengers=payload.passengers,
            concession=payload.concession,
            filters=payload.filters,
        )

        return TransportSearchResponse(is_mock=True, results=results)
    except Exception as e:
        raise AppError(500, "transport_search_failed", str(e))
