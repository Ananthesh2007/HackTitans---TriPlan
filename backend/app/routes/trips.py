from fastapi import APIRouter

from app.ai.coordinator import (
    PlanValidationError,
    generate_itinerary,
    modify_itinerary,
    validate_plan,
)
from app.errors import AppError
from app.models.trip import ModifyRequest, ModifyResponse, Trip, TripRequest
from app.services.budget import estimate_budget, flag_budget_issues
from app.store import TRIPS, save_trip, get_trip, delete_trip

router = APIRouter(prefix="/api/trips", tags=["trips"])


@router.post("", response_model=Trip, response_model_exclude_none=True)
def create_trip(payload: TripRequest):
    """Create a new trip and generate an itinerary."""
    try:
        trip = generate_itinerary(payload)
    except PlanValidationError as exc:
        # The AI answered, but the answer did not match the agreed schema.
        raise AppError(
            502,
            "invalid_ai_output",
            "The AI returned a plan we could not use. Please try again.",
            {"issues": exc.errors},
        )
    except Exception as exc:  # noqa: BLE001 - never let the server crash
        raise AppError(500, "trip_generation_failed", "Could not generate the itinerary.")

    # The budget comes from deterministic code, not from the AI.
    trip.estimated_costs = estimate_budget(trip)

    # Save trip to database
    # Date: 20-10-2026 — Database persistence replaces in-memory storage
    # Never report a trip as saved if the database fails
    saved = save_trip(trip.trip_id, trip.model_dump())
    if not saved:
        # Database failed, but trip is in memory cache
        # Add a warning to the response
        trip.warning = "Trip created but not persisted. Data may be lost on server restart."

    return trip


@router.get("/{trip_id}", response_model=Trip, response_model_exclude_none=True)
def retrieve_trip(trip_id: str):
    """Retrieve a saved trip by ID."""
    # Try database first (production storage)
    trip_data = get_trip(trip_id)

    if not trip_data:
        raise AppError(404, "trip_not_found", f"Trip '{trip_id}' not found.")

    # Convert to Trip model
    return Trip(**trip_data)


@router.post("/{trip_id}/modify", response_model=ModifyResponse, response_model_exclude_none=True)
def modify_trip(trip_id: str, payload: ModifyRequest):
    """Modify a trip itinerary based on a user message."""
    # Get from database
    trip_data = get_trip(trip_id)
    if not trip_data:
        raise AppError(404, "trip_not_found", f"Trip '{trip_id}' not found.")

    current = Trip(**trip_data)

    try:
        proposed = modify_itinerary(current, payload.message)
    except PlanValidationError as exc:
        raise AppError(
            502,
            "invalid_ai_output",
            "The AI returned a change we could not use. Please try again.",
            {"issues": exc.errors},
        )
    except Exception:  # noqa: BLE001 - never let the server crash
        raise AppError(500, "modification_failed", "Could not modify the itinerary.")

    # The revised plan must pass validation before the user sees it.
    issues = validate_plan(proposed)
    if issues:
        raise AppError(
            422,
            "invalid_plan",
            "The revised itinerary did not pass validation.",
            {"issues": issues},
        )

    # Recalculate the budget for the revised plan.
    proposed.estimated_costs = estimate_budget(proposed)

    # Save modified trip to database
    # Date: 20-10-2026 — Save modifications to database
    save_trip(proposed.trip_id, proposed.model_dump())

    return ModifyResponse(
        reply=proposed.reply or "Your trip has been updated based on your request.",
        trip=proposed,
    )


@router.post("/{trip_id}/budget", response_model=dict)
def calculate_budget(trip_id: str):
    """Calculate or recalculate the budget for a trip."""
    trip_data = get_trip(trip_id)
    if not trip_data:
        raise AppError(404, "trip_not_found", f"Trip '{trip_id}' not found.")

    trip = Trip(**trip_data)
    costs = estimate_budget(trip)
    flags = flag_budget_issues(trip.budget, costs.total or 0)

    return {
        "trip_id": trip_id,
        "estimated_costs": costs.model_dump(),
        "budget_status": flags,
    }
