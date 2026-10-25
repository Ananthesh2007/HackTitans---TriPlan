"""AI coordination module for itinerary generation and modification.

This module calls Member 3's AI layer (`app/ai/llm.py` and
`app/ai/prompts.py`) to produce structured itinerary data.

The backend never lets a provider problem become a server crash:

- No API key configured  -> use the built-in mock itinerary.
- Provider times out, errors, or returns invalid JSON
                         -> use the mock itinerary and mark the trip
                            with `is_mock=True` and a warning.
- The model returns JSON that does not match the schema
                         -> the trip is rejected as invalid and a clear
                            error is raised to the route layer.
"""

import copy
import logging
import re
import time
import uuid
from typing import Generator, List

from app import config
from app.ai.llm import LLMError, ask_for_json, stream_modification_answer
from app.ai.prompts import (
    ITINERARY_RESPONSE_FORMAT,
    MODIFICATION_RESPONSE_FORMAT,
    build_itinerary_prompt,
    build_modification_prompt,
)
from app.models.trip import Activity, DayPlan, Trip
from app.services.budget import estimate_budget

logger = logging.getLogger("triplan.coordinator")


class PlanValidationError(Exception):
    """The model's answer was valid JSON but did not match the schema."""

    def __init__(self, errors: List[str]):
        super().__init__("; ".join(errors))
        self.errors = errors


def generate_itinerary(trip_request) -> Trip:
    """Generate an itinerary for a validated trip request.

    Uses the real AI provider when one is configured. Falls back to the
    built-in mock itinerary when the provider is missing, unreachable or
    returns unusable output, so the user always gets a plan.

    Args:
        trip_request: The validated TripRequest.

    Returns:
        A Trip with a day-wise itinerary and a deterministic budget.
    """
    trip_id = str(uuid.uuid4())
    itinerary: List[DayPlan]
    is_mock = True
    warning: str | None = None

    if config.is_ai_configured():
        try:
            answer = ask_for_json(
                build_itinerary_prompt(trip_request),
                response_format=ITINERARY_RESPONSE_FORMAT,
            )
            itinerary = _build_itinerary_from_answer(answer, trip_request.days)
            is_mock = False
        except LLMError as exc:
            # Provider is down, timed out, or answered with broken JSON.
            logger.warning("AI itinerary generation failed, using the mock plan: %s", exc)
            warning = "The AI service was unavailable, so this is a sample itinerary."
            itinerary = generate_mock_itinerary(trip_request.destination, trip_request.days)
        except PlanValidationError as exc:
            # The model answered, but the answer did not match the schema.
            logger.warning("AI itinerary did not match the schema: %s", exc.errors)
            raise
    else:
        warning = "The AI service is not configured, so this is a sample itinerary."
        itinerary = generate_mock_itinerary(trip_request.destination, trip_request.days)

    trip = Trip(
        trip_id=trip_id,
        is_mock=is_mock,
        is_estimate=True,  # every cost from the AI is a suggestion, not a price
        origin=trip_request.origin,
        destination=trip_request.destination,
        travel_date=trip_request.travel_date,
        days=trip_request.days,
        people=trip_request.people,
        budget=trip_request.budget,
        currency="INR",
        interests=list(trip_request.interests),
        diet=trip_request.diet,
        itinerary=itinerary,
    )

    # The budget is computed by deterministic code, never by the model.
    trip.estimated_costs = estimate_budget(trip)

    if warning:
        trip.warning = warning

    return trip


def modify_itinerary(current_trip: Trip, message: str, history: list | None = None) -> Trip:
    """Modify a trip itinerary from a natural-language request.

    Keeps the trip context (destination, budget, days, interests, diet) and
    asks the model for a revised plan. The caller validates the result with
    `validate_plan` before showing it to the user.

    Args:
        current_trip: The trip being edited.
        message: What the user asked for.
        history: Prior conversation turns.

    Returns:
        The proposed revised Trip.
    """
    if not config.is_ai_configured():
        trip = copy.deepcopy(current_trip)
        reply, warning = _mock_modification(trip, message)
        trip.reply = reply
        trip.warning = warning
        trip.estimated_costs = estimate_budget(trip)
        return trip

    try:
        answer = ask_for_json(
            build_modification_prompt(current_trip, message, history),
            response_format=MODIFICATION_RESPONSE_FORMAT,
        )
    except LLMError as exc:
        logger.warning("AI modification failed, using the mock change: %s", exc)
        trip = copy.deepcopy(current_trip)
        reply, warning = _mock_modification(trip, message)
        trip.reply = reply
        trip.warning = warning
        trip.estimated_costs = estimate_budget(trip)
        return trip

    itinerary = _build_itinerary_from_answer(answer, current_trip.days)

    trip = copy.deepcopy(current_trip)
    trip.itinerary = itinerary
    trip.estimated_costs = estimate_budget(trip)
    trip.reply = str(answer.get("reply") or "Your trip has been updated.")
    trip.warning = None

    return trip


def _chunk_reply(text: str) -> list[str]:
    """Break reply text into small natural word/token units for streaming."""
    return re.findall(r"\S+|\s+", text) or [text]


def stream_modify_itinerary(
    current_trip: Trip,
    message: str,
    history: list | None = None,
) -> Generator[tuple[str, str | Trip], None, None]:
    """Stream reply tokens and yield the final revised Trip plan.

    Yields:
        ("token", str): Token deltas for real-time assistant response display.
        ("done", Trip): The proposed revised Trip object once complete.
    """
    if not config.is_ai_configured():
        trip = copy.deepcopy(current_trip)
        reply, warning = _mock_modification(trip, message)
        trip.reply = reply
        trip.warning = warning
        trip.estimated_costs = estimate_budget(trip)

        for chunk in _chunk_reply(reply):
            yield ("token", chunk)
            time.sleep(0.015)

        yield ("done", trip)
        return

    try:
        prompt = build_modification_prompt(current_trip, message, history)
        generator = stream_modification_answer(
            prompt,
            response_format=MODIFICATION_RESPONSE_FORMAT,
        )
        while True:
            try:
                token = next(generator)
                yield ("token", token)
            except StopIteration as stop:
                answer = stop.value
                break

        itinerary = _build_itinerary_from_answer(answer, current_trip.days)
        trip = copy.deepcopy(current_trip)
        trip.itinerary = itinerary
        trip.estimated_costs = estimate_budget(trip)
        trip.reply = str(answer.get("reply") or "Your trip has been updated.")
        trip.warning = None
        yield ("done", trip)
    except (LLMError, PlanValidationError) as exc:
        logger.warning("AI streaming modification failed, using mock change: %s", exc)
        trip = copy.deepcopy(current_trip)
        reply, warning = _mock_modification(trip, message)
        trip.reply = reply
        trip.warning = warning
        trip.estimated_costs = estimate_budget(trip)

        for chunk in _chunk_reply(reply):
            yield ("token", chunk)
            time.sleep(0.015)

        yield ("done", trip)


def validate_plan(trip: Trip) -> List[str]:
    """Validate a trip's itinerary structure.

    Returns a list of error messages if validation fails, or an empty list
    if the plan is valid. Structural checks only.

    Called by POST /api/trips/{trip_id}/modify to validate revised plans.
    """
    errors: List[str] = []

    if not trip.trip_id:
        errors.append("Trip must have a trip_id")

    if not trip.destination:
        errors.append("Trip must have a destination")

    if not trip.itinerary:
        errors.append("Trip must have an itinerary")

    for day in trip.itinerary:
        if not day.title:
            errors.append(f"Day {day.day} must have a title")

        for index, activity in enumerate(day.activities):
            label = f"Day {day.day} activity {index + 1}"
            if not activity.name:
                errors.append(f"{label} must have a name")
            if not activity.location:
                errors.append(f"{label} must have a location")
            if activity.estimated_cost < 0:
                errors.append(f"{label} has an invalid cost")

    return errors


def generate_mock_itinerary(destination: str, days: int) -> List[DayPlan]:
    """Generate a structured mock itinerary for the destination.

    The plan always has exactly `days` days with 3 activities each, so it
    matches the agreed contract (see docs/api-contract.md).
    """
    itinerary = []

    # Common activities for demonstration (structured data matching contract)
    activities_pool = [
        ("09:00", "Local sightseeing tour", "City centre", 100),
        ("14:00", "Cultural museum visit", "Old town", 200),
        ("11:00", "Nature walk", "National park", 300),
        ("16:00", "Traditional food experience", "Local market", 150),
        ("18:30", "Riverside stroll", "Waterfront", 120),
        ("20:00", "Street food dinner", "Night market", 350),
    ]

    activities_per_day = 3

    for day_num in range(1, days + 1):
        # Take a rotating window of the pool so each day gets 3 activities.
        start = (day_num - 1) % len(activities_pool)
        selected = [
            activities_pool[(start + offset) % len(activities_pool)]
            for offset in range(activities_per_day)
        ]

        # Show the activities in the order they happen during the day.
        selected.sort(key=lambda item: item[0])

        day_plan = DayPlan(
            day=day_num,
            title=f"Day {day_num} in {destination}",
            activities=[
                # The location carries the destination, matching the contract
                # and what the model is asked to return.
                Activity(time=t, name=n, location=f"{l}, {destination}", estimated_cost=c)
                for t, n, l, c in selected
            ]
        )
        itinerary.append(day_plan)

    return itinerary


# ---------- Internals ----------


def _build_itinerary_from_answer(answer: dict, expected_days: int) -> List[DayPlan]:
    """Turn a model answer into a list of DayPlan objects.

    Raises:
        PlanValidationError: when the answer does not match the schema.
    """
    raw_days = answer.get("itinerary")

    if not isinstance(raw_days, list) or not raw_days:
        raise PlanValidationError(["The model answer did not include an 'itinerary' list."])

    errors: List[str] = []
    days: List[DayPlan] = []

    for index, raw_day in enumerate(raw_days):
        if not isinstance(raw_day, dict):
            errors.append(f"Day {index + 1} is not an object.")
            continue

        activities = _build_activities(raw_day.get("activities"), index + 1, errors)
        if activities is None:
            continue

        days.append(
            DayPlan(
                day=_as_int(raw_day.get("day"), index + 1),
                title=str(raw_day.get("title") or f"Day {index + 1}"),
                activities=activities,
            )
        )

    if errors:
        raise PlanValidationError(errors)

    if len(days) != expected_days:
        raise PlanValidationError(
            [f"The model returned {len(days)} days but the trip needs {expected_days}."]
        )

    return days


def _build_activities(raw_activities, day_number: int, errors: List[str]):
    """Turn the 'activities' list of one day into Activity objects."""
    if not isinstance(raw_activities, list) or not raw_activities:
        errors.append(f"Day {day_number} has no activities.")
        return None

    activities: List[Activity] = []

    for index, raw_activity in enumerate(raw_activities):
        if not isinstance(raw_activity, dict):
            errors.append(f"Day {day_number} activity {index + 1} is not an object.")
            continue

        name = str(raw_activity.get("name") or "").strip()
        location = str(raw_activity.get("location") or "").strip()
        time = str(raw_activity.get("time") or "").strip()

        if not name:
            errors.append(f"Day {day_number} activity {index + 1} has no name.")
        if not location:
            errors.append(f"Day {day_number} activity {index + 1} has no location.")

        cost = _as_float(raw_activity.get("estimated_cost"), 0.0)
        if cost < 0:
            errors.append(f"Day {day_number} activity {index + 1} has a negative cost.")

        activities.append(
            Activity(
                time=time or "09:00",
                name=name or "Free time",
                location=location or "To be decided",
                estimated_cost=cost,
            )
        )

    if not activities:
        errors.append(f"Day {day_number} has no usable activities.")
        return None

    return activities


def _as_int(value, fallback: int) -> int:
    """Read an integer from the model answer without crashing."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def _as_float(value, fallback: float) -> float:
    """Read a number from the model answer without crashing."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


def _mock_modification(trip: Trip, message: str) -> tuple[str, str]:
    """Apply a simple change to a trip when no AI provider is available.

    Returns:
        A short reply for the user and a warning to show above the plan.
    """
    lowered = message.lower()

    # Detect flight search queries and guide user to the flights page
    if any(word in lowered for word in ("flight", "flights", "fly", "airline", "indigo", "air india", "akasa")):
        return (
            "You can compare real-time fares and schedules directly on our Flights page below. It lets you filter by price, departure window, and airline concessions without needing an AI key. Would you like me to recommend the best time of day to fly out?",
            None,
        )

    # Detect hotel search queries
    if any(word in lowered for word in ("hotel", "hotels", "accommodation", "stay", "room", "resort")):
        return (
            "Head over to our Hotels section right below to explore places to stay with filters for neighborhood, amenities, and nightly rates. What kind of vibe are you leaning towards for your stay—something central or a quiet retreat?",
            None,
        )

    # Detect transport search queries
    if any(word in lowered for word in ("bus", "buses", "train", "trains", "transport", "ksrtc", "redbus", "irctc")):
        return (
            "Check out our Transport tab below to search buses and trains with AC, sleeper, and live-tracking filters. Are you looking for the fastest route or an overnight sleeper to save on travel time?",
            None,
        )

    target = None
    target_cost = 0.0
    for day_index, day in enumerate(trip.itinerary):
        for activity_index, activity in enumerate(day.activities):
            cost = float(activity.estimated_cost)
            if cost > target_cost:
                target_cost = cost
                target = (day_index, activity_index)

    if target and any(word in lowered for word in ("remove", "drop", "delete", "skip", "less", "cheaper")):
        day_index, activity_index = target
        removed = trip.itinerary[day_index].activities.pop(activity_index)
        return (
            f"I've removed '{removed.name}' from day {trip.itinerary[day_index].day} to help lower your expenses. What other parts of the plan would you like to tweak?",
            "The AI service is not configured, so this change was made with a simple rule.",
        )

    return (
        f"I've kept your itinerary handy while we chat. You can search flights, hotels, and transport anytime below. What else would you like to explore or adjust for your trip to {trip.destination}?",
        None,
    )
