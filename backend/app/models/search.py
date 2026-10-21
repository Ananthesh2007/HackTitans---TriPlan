import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.models.common import Place, different_places, not_in_past


# ---------- Filters ----------
# The concession categories a traveller can pick. The same list is used by the
# frontend, and it is written down in docs/api-contract.md.
Concession = Literal["senior_citizen", "army", "student", "doctor", "nurse"]

# The filters the user picks on a search page. The frontend applies them to
# the results it gets back; a live provider would use them to narrow the
# search as well.
class SearchFilters(BaseModel):
    """The filters a search page sends with the search."""

    # "any", "ac" or "non_ac"
    ac: Literal["any", "ac", "non_ac"] = "any"
    # "any", "seater" or "sleeper"
    seat_class: Literal["any", "seater", "sleeper"] = "any"
    # Only services that can be tracked live.
    tracking: bool = False
    # Only new vehicles.
    is_new: bool = False
    price_min: float | None = Field(default=None, ge=0)
    price_max: float | None = Field(default=None, ge=0)
    # "any", "night", "morning", "afternoon" or "evening"
    departure_window: Literal["any", "night", "morning", "afternoon", "evening"] = "any"
    # "recommended", "price_asc", "price_desc", "departure_asc",
    # "departure_desc", "duration_asc" or "name_asc"
    sort: str = "recommended"


# ---------- Requests ----------
class TravelSearchRequest(BaseModel):
    """Shared by flights, buses and trains."""

    origin: Place
    destination: Place
    date: datetime.date
    passengers: int = Field(ge=1, le=9)
    # The concession the traveller will use, if any.
    concession: Concession | None = None
    # The filters picked on the page.
    filters: SearchFilters | None = None

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
    # Implied by the number of guests, but the contract asks for it.
    rooms: int = Field(default=1, ge=1, le=10)
    # The concession the traveller will use, if any.
    concession: Concession | None = None
    # The filters picked on the page.
    filters: SearchFilters | None = None

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
    # The concessions the provider offers on this fare.
    concessions: list[Concession] = Field(default_factory=list)


class HotelResult(BaseModel):
    id: str
    name: str | None = None
    area: str | None = None
    price_per_night: float | None = Field(default=None, ge=0)
    currency: str = "INR"
    booking_url: str | None = None
    # The time the room can be checked into, as "HH:MM".
    check_in_time: str | None = None
    # The concessions the provider offers on this rate.
    concessions: list[Concession] = Field(default_factory=list)


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
    # True when the service can be tracked live.
    tracking: bool = False
    # True when the vehicle is a new one.
    is_new: bool = False
    # The concessions the provider offers on this fare.
    concessions: list[Concession] = Field(default_factory=list)


class FlightSearchResponse(BaseModel):
    is_mock: bool = False
    results: list[FlightResult]


class HotelSearchResponse(BaseModel):
    is_mock: bool = False
    results: list[HotelResult]


class TransportSearchResponse(BaseModel):
    is_mock: bool = False
    results: list[TransportResult]
