from fastapi import APIRouter

from app.errors import AppError
from app.models.search import FlightSearchRequest, FlightSearchResponse

router = APIRouter(prefix="/api/flights", tags=["flights"])


@router.post("/search", response_model=FlightSearchResponse)
def search_flights(payload: FlightSearchRequest):
    raise AppError(501, "not_implemented", "Flight search is not built yet. It arrives on Day 8.")