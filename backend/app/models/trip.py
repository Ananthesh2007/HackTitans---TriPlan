import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.models.common import Place, not_in_past

Interest = Literal[
    "nature", "food", "adventure", "culture", "history", "beaches", "relaxation", "shopping"
]
Diet = Literal["none", "vegetarian", "vegan", "non-vegetarian"]


# ---------- Request: POST /api/trips ----------
class TripRequest(BaseModel):
    # Optional: the frontend omits it when "Travelling from" is left blank.
    origin: Place | None = None
    destination: Place
    days: int = Field(ge=1, le=30)
    budget: float = Field(gt=0, le=100_000_000)
    people: int = Field(ge=1, le=20)
    travel_date: datetime.date
    interests: list[Interest] = Field(default_factory=list, max_length=8)
    diet: Diet = "none"

    @field_validator("travel_date")
    @classmethod
    def travel_date_not_in_past(cls, value):
        return not_in_past(value)


# ---------- The trip itself (response shape) ----------
class Activity(BaseModel):
    time: str
    name: str
    location: str
    estimated_cost: float = Field(ge=0)


class DayPlan(BaseModel):
    day: int = Field(ge=1)
    title: str
    activities: list[Activity]


class EstimatedCosts(BaseModel):
    flights: float | None = Field(default=None, ge=0)
    accommodation: float | None = Field(default=None, ge=0)
    food: float | None = Field(default=None, ge=0)
    activities: float | None = Field(default=None, ge=0)
    local_transport: float | None = Field(default=None, ge=0)
    total: float | None = Field(default=None, ge=0)


class Trip(BaseModel):
    trip_id: str
    is_mock: bool = False
    is_estimate: bool = True  # AI-generated costs are always estimates
    origin: str | None = None
    destination: str
    travel_date: datetime.date | None = None
    days: int = Field(ge=1)
    people: int = Field(ge=1)
    budget: float = Field(gt=0)
    currency: str = "INR"
    # Kept so the AI can modify a trip without losing the user's preferences.
    interests: list[Interest] = Field(default_factory=list, max_length=8)
    diet: Diet = "none"
    estimated_costs: EstimatedCosts | None = None
    itinerary: list[DayPlan]
    # Set when the AI provider was unavailable, so the frontend can say so.
    warning: str | None = None
    # Set by modify_itinerary with the assistant's short reply.
    reply: str | None = None


# ---------- POST /api/trips/{trip_id}/modify ----------
class ModifyRequest(BaseModel):
    message: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
    current_trip: Trip | None = None


class ModifyResponse(BaseModel):
    reply: str
    trip: Trip  # the PROPOSED plan; the user must choose Apply in the frontend# 19-10-2026 — Input limits added (max_length=80 for places, le=30 days, etc.)
