from fastapi import APIRouter

from app.errors import AppError
from app.models.search import TransportSearchRequest, TransportSearchResponse

router = APIRouter(prefix="/api/transport", tags=["transport"])


@router.post("/search", response_model=TransportSearchResponse)
def search_transport(payload: TransportSearchRequest):
    raise AppError(501, "not_implemented", "Bus and train search is not built yet. It arrives on Day 8.")