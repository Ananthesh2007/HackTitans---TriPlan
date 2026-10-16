from fastapi import APIRouter

from app.errors import AppError
from app.models.search import HotelSearchRequest, HotelSearchResponse

router = APIRouter(prefix="/api/hotels", tags=["hotels"])


@router.post("/search", response_model=HotelSearchResponse)
def search_hotels(payload: HotelSearchRequest):
    raise AppError(501, "not_implemented", "Hotel search is not built yet. It arrives on Day 8.")