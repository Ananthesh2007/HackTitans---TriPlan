"""Deterministic budget estimation service.

Date modified: 14-10-2026 — all figures labeled as estimates.
Date modified: 20-10-2026 — activities cost now comes from the plan itself.
Every value is deterministic (no AI guess). No live price data is claimed.
"""

from app.models.trip import Trip, EstimatedCosts


def estimate_budget(trip: Trip) -> EstimatedCosts:
    """Estimate trip costs based on deterministic formulas.

    Flights, accommodation, food and local transport use fixed per-person
    rates, because no live provider is integrated and the model is asked not
    to price them (see app/ai/prompts.py).

    Activities are different: the plan already carries a per-person cost for
    every activity, so the estimate is the sum of those costs. That keeps the
    budget card consistent with the itinerary shown on the dashboard, and it
    makes the estimate move when the itinerary changes.

    Args:
        trip: The trip object with days, people, destination

    Returns:
        EstimatedCosts object with all cost categories as estimates
    """
    days = trip.days
    people = trip.people

    # Deterministic per-person cost estimates (in INR)
    flights_per_person = 4800
    accommodation_per_night = 2000
    food_per_day = 1000
    activities_per_day_fallback = 800
    local_transport_per_day = 500

    total_flights = flights_per_person * people
    total_accommodation = accommodation_per_night * days * people
    total_food = food_per_day * days * people
    total_transport = local_transport_per_day * days * people

    # Prefer the costs the plan itself carries. Fall back to the flat rate
    # only when there is no itinerary to read them from.
    plan_activities_per_person = sum(
        activity.estimated_cost
        for day in trip.itinerary
        for activity in day.activities
    )
    if plan_activities_per_person > 0:
        total_activities = plan_activities_per_person * people
    else:
        total_activities = activities_per_day_fallback * days * people

    grand_total = (
        total_flights + total_accommodation + total_food + total_activities + total_transport
    )

    return EstimatedCosts(
        flights=float(total_flights),
        accommodation=float(total_accommodation),
        food=float(total_food),
        activities=float(total_activities),
        local_transport=float(total_transport),
        total=float(grand_total),
    )


def flag_budget_issues(budget: float, estimate: float) -> dict:
    """Compare user budget against estimate and flag issues.
    
    Returns a dict with budget status information.
    """
    is_below = budget < estimate
    shortfall = estimate - budget if is_below else 0.0
    
    return {
        "budget": float(budget),
        "estimate": float(estimate),
        "is_below_estimate": is_below,
        "shortfall": float(shortfall),
        "message": None if not is_below else (
            f"Your estimated costs (₹{estimate:,.0f}) exceed your budget (₹{budget:,.0f}). "
            f"Consider adjusting your trip or increasing your budget."
        ),
    }
