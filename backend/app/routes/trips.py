from fastapi import APIRouter

from app.errors import AppError
from app.models.trip import ModifyRequest, ModifyResponse, Trip, TripRequest

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("", response_model=Trip, response_model_exclude_none=True)
def create_trip(payload: TripRequest):
    raise AppError(501, "not_implemented", "Trip creation is not built yet. It arrives on Day 3.")


@router.post("/{trip_id}/modify", response_model=ModifyResponse, response_model_exclude_none=True)
def modify_trip(trip_id: str, payload: ModifyRequest):
    raise AppError(501, "not_implemented", "Trip changes are not built yet. They arrive on Day 7.")