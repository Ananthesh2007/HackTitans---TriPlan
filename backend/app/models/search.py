import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.common import Place, different_places, not_in_past


# ---------- Requests ----------
class TravelSearchRequest(BaseModel):
    """Shared by flights, buses and trains."""

    origin: Place
    destination: Place
    date: datetime.date
    passengers: int = Field(ge=1, le=9)

    @field_validator("destination")
    @classmethod
    def destination_differs(cls, value, info):
        return different_places(info.data.get("origin"), value)

    @field_validator("date")
    @classmethod
    def date_not_in_past(cls, value):
        return not_in_past(value)


class FlightSearchRequest(TravelSearchRequest):
    pass


class TransportSearchRequest(TravelSearchRequest):
    mode: Literal["bus", "train"]


class HotelSearchRequest(BaseModel):
    destination: Place
    check_in: datetime.date
    check_out: datetime.date
    guests: int = Field(ge=1, le=20)

    @field_validator("check_in")
    @classmethod
    def check_in_not_in_past(cls, value):
        return not_in_past(value)

    @field_validator("check_out")
    @classmethod
    def check_out_after_check_in(cls, value, info):
        check_in = info.data.get("check_in")
        if check_in and value <= check_in:
            raise ValueError("Check-out must be after check-in.")
        return value


# ---------- Results ----------
class FlightResult(BaseModel):
    id: str
    airline: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    duration: str | None = None
    stops: int | None = Field(default=None, ge=0)
    price: float | None = Field(default=None, ge=0)  # per person
    currency: str = "INR"
    booking_url: str | None = None  # https only; checked on Day 8


class HotelResult(BaseModel):
    id: str
    name: str | None = None
    area: str | None = None
    price_per_night: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    booking_url: str | None = None


class TransportResult(BaseModel):
    id: str
    operator: str | None = None
    vehicle_type: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    duration: str | None = None
    price: float | None = Field(default=None, ge=0)  # per person
    currency: str = "INR"
    booking_url: str | None = None


class FlightSearchResponse(BaseModel):
    is_mock: bool = False
    results: list[FlightResult]


class HotelSearchResponse(BaseModel):
    is_mock: bool = False
    results: list[HotelResult]


class TransportSearchResponse(BaseModel):
    is_mock: bool = False
    results: list[TransportResult]