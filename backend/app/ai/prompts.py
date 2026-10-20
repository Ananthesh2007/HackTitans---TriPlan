"""Prompts for the AI coordinator.

Member 3 (AI developer) owns the wording of these prompts and the JSON
shape the model must return. The backend only guarantees that the request
is built here and that the answer is parsed into the Pydantic models in
`app/models/trip.py`.

Rules the model must follow:
- Answer with JSON only. No markdown fences, no commentary.
- Never invent live prices. Activity costs are rough estimates in INR.
- Never invent opening hours or ticket availability.
"""

# The JSON shape the model must return for a full itinerary.
ITINERARY_RESPONSE_FORMAT = {
    "type": "json_object",
}

# The JSON shape the model must return for a modification.
MODIFICATION_RESPONSE_FORMAT = {
    "type": "json_object",
}


def build_itinerary_prompt(trip) -> str:
    """Build the prompt that asks the model for a day-wise itinerary.

    Args:
        trip: The validated TripRequest from the user.

    Returns:
        The prompt text to send to the LLM.
    """
    interests = ", ".join(trip.interests) if trip.interests else "general sightseeing"
    diet = trip.diet if trip.diet and trip.diet != "none" else "no specific diet"

    return f"""You are TriPlan's trip planner. Plan a {trip.days}-day trip.

Trip details:
- Origin: {trip.origin}
- Destination: {trip.destination}
- Travel date: {trip.travel_date}
- Travellers: {trip.people}
- Budget: {trip.budget} INR (total for the whole group)
- Interests: {interests}
- Diet: {diet}

Return JSON only, in exactly this shape:

{{
  "itinerary": [
    {{
      "day": 1,
      "title": "Short title for day 1",
      "activities": [
        {{
          "time": "09:00",
          "name": "Activity name",
          "location": "Place name, {trip.destination}",
          "estimated_cost": 500
        }}
      ]
    }}
  ]
}}

Rules:
- Exactly {trip.days} objects in "itinerary", with "day" numbered 1 to {trip.days}.
- Each day must have between 3 and 5 activities.
- "time" must be a 24-hour clock string such as "09:00" or "16:30".
- "estimated_cost" is a rough per-person estimate in INR. It must be a number.
- Keep the whole plan close to the {trip.budget} INR budget.
- Respect the traveller interests and the diet. Suggest vegetarian or vegan
  food options when the diet requires it.
- Group nearby attractions on the same day and keep travel between them short.
- Do not include prices for flights or hotels. Those are added by the budget
  service, not by you.
- Do not add commentary, markdown fences or any text outside the JSON.
"""


def build_modification_prompt(current_trip, message: str) -> str:
    """Build the prompt that asks the model to revise a current itinerary.

    Args:
        current_trip: The Trip the user is editing.
        message: The user's natural-language request.

    Returns:
        The prompt text to send to the LLM.
    """
    days = len(current_trip.itinerary)
    interests = ", ".join(current_trip.interests) if current_trip.interests else "general sightseeing"
    diet = current_trip.diet if current_trip.diet and current_trip.diet != "none" else "no specific diet"

    return f"""You are TriPlan's trip planner. Revise an existing itinerary.

Current trip:
- Destination: {current_trip.destination}
- Days: {days}
- Travellers: {current_trip.people}
- Budget: {current_trip.budget} INR (total for the whole group)
- Interests: {interests}
- Diet: {diet}

User request:
{message}

Current itinerary:
{current_trip.model_dump_json(indent=2)}

Return JSON only, in exactly this shape:

{{
  "reply": "One or two sentences telling the user what you changed.",
  "itinerary": [
    {{
      "day": 1,
      "title": "Short title for day 1",
      "activities": [
        {{
          "time": "09:00",
          "name": "Activity name",
          "location": "Place name, {current_trip.destination}",
          "estimated_cost": 500
        }}
      ]
    }}
  ]
}}

Rules:
- Keep exactly {days} days, numbered 1 to {days}.
- Keep between 3 and 5 activities per day.
- Apply the user's request to the itinerary, not just to the reply text.
- "estimated_cost" is a rough per-person estimate in INR. It must be a number.
- Keep the plan close to the {current_trip.budget} INR budget.
- Respect the traveller interests and the diet.
- Do not add commentary, markdown fences or any text outside the JSON.
"""
