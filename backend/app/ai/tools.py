"""Tools the AI can call while planning a trip.

The planner (`app/ai/coordinator.py`) talks to a provider that only speaks
JSON. This module gives it a small, fixed set of tools it can ask for, so
the model can look up real prices and real places instead of guessing.

The tools are thin wrappers around the service layer:

- `search_flights`, `search_hotels` -> `app/services/flights.py`, `hotels.py`
- `search_transport` -> `app/services/transport.py`
- `geocode_place`, `suggest_stop_order` -> `app/services/maps.py`
- `estimate_trip_cost` -> `app/services/budget.py`

Rules for this file:
- The tool definitions are plain data, so the same list works with any
  provider that speaks the OpenAI function-calling format.
- Every failure mode (bad arguments, a service that is down, a provider
  with no data) comes back as a normal return value. Nothing here raises
  past `call_tool`, so a bad tool call never breaks a trip.
- Nothing is invented. A tool that has no data says so, instead of making
  a price or a coordinate up.
- The tool results are JSON-serialisable, because they are sent straight
  back to the model as the content of a `tool` message.
"""

import copy
import datetime
import json
import logging
from typing import Any, Callable

from pydantic import ValidationError

from app.models.maps import RouteStop
from app.models.search import (
    FlightSearchRequest,
    HotelSearchRequest,
    TransportSearchRequest,
)
from app.models.trip import Activity, DayPlan, Trip
from app.services.budget import estimate_budget
from app.services.flights import search_flights
from app.services.hotels import search_hotels
from app.services.maps import geocode_place, suggest_visit_order
from app.services.transport import search_transport

logger = logging.getLogger("triplan.tools")


# ---------- Tool definitions ----------

# How many places one call to `suggest_stop_order` may look up.
MAX_STOPS_PER_CALL = 8


def _tool(
    name: str,
    description: str,
    properties: dict,
    required: list[str],
) -> dict:
    """Build one function-calling definition."""
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


TOOL_DEFINITIONS: list[dict] = [
    _tool(
        "search_flights",
        "Search flights between two places. Returns sample fares in INR.",
        {
            "origin": {"type": "string", "description": "Departure city."},
            "destination": {"type": "string", "description": "Arrival city."},
            "date": {
                "type": "string",
                "description": "Departure date, YYYY-MM-DD. Today or later.",
            },
            "passengers": {
                "type": "integer",
                "description": "Number of travellers, 1 to 9.",
                "minimum": 1,
                "maximum": 9,
            },
            "concession": {
                "type": "string",
                "description": (
                    "The concession category of the traveller, if any. "
                    "Leave it out when nobody is travelling with a concession."
                ),
                "enum": list(CONCESSIONS),
            },
        },
        ["origin", "destination", "date", "passengers"],
    ),
    _tool(
        "search_hotels",
        "Search places to stay in a destination. Returns sample rates in INR.",
        {
            "destination": {"type": "string", "description": "City or area to stay in."},
            "check_in": {
                "type": "string",
                "description": "Check-in date, YYYY-MM-DD. Today or later.",
            },
            "check_out": {
                "type": "string",
                "description": "Check-out date, YYYY-MM-DD. After check-in.",
            },
            "guests": {
                "type": "integer",
                "description": "Number of guests, 1 to 20.",
                "minimum": 1,
                "maximum": 20,
            },
            "concession": {
                "type": "string",
                "description": (
                    "The concession category of the traveller, if any. "
                    "Leave it out when nobody is travelling with a concession."
                ),
                "enum": list(CONCESSIONS),
            },
        },
        ["destination", "check_in", "check_out", "guests"],
    ),
    _tool(
        "search_transport",
        "Search buses or trains between two places. Returns sample fares in INR.",
        {
            "origin": {"type": "string", "description": "Departure city."},
            "destination": {"type": "string", "description": "Arrival city."},
            "date": {
                "type": "string",
                "description": "Travel date, YYYY-MM-DD. Today or later.",
            },
            "passengers": {
                "type": "integer",
                "description": "Number of travellers, 1 to 9.",
                "minimum": 1,
                "maximum": 9,
            },
            "mode": {
                "type": "string",
                "description": "The kind of transport to look for.",
                "enum": ["bus", "train"],
            },
            "concession": {
                "type": "string",
                "description": (
                    "The concession category of the traveller, if any. "
                    "Leave it out when nobody is travelling with a concession."
                ),
                "enum": list(CONCESSIONS),
            },
        },
        ["origin", "destination", "date", "passengers", "mode"],
    ),
    _tool(
        "geocode_place",
        "Look up one place name and return where it is on the map.",
        {
            "place": {
                "type": "string",
                "description": "Name of the place, for example 'Cubbon Park, Bengaluru'.",
            }
        },
        ["place"],
    ),
    _tool(
        "suggest_stop_order",
        (
            "Order a list of places so nearby places are visited together. "
            "Returns the places in a suggested visiting order."
        ),
        {
            "places": {
                "type": "array",
                "description": (
                    "The places of one day, in any order. "
                    f"At most {MAX_STOPS_PER_CALL} places."
                ),
                "items": {"type": "string"},
            }
        },
        ["places"],
    ),
    _tool(
        "estimate_trip_cost",
        (
            "Work out the estimated cost of a trip with the deterministic "
            "budget formulas. Use this instead of adding up prices yourself."
        ),
        {
            "days": {
                "type": "integer",
                "description": "Number of days of the trip, 1 to 30.",
                "minimum": 1,
                "maximum": 30,
            },
            "people": {
                "type": "integer",
                "description": "Number of travellers, 1 to 20.",
                "minimum": 1,
                "maximum": 20,
            },
            "activity_costs": {
                "type": "array",
                "description": (
                    "The per-person cost of every activity in the plan, in INR. "
                    "Leave it out when the plan has no activities yet."
                ),
                "items": {"type": "number", "minimum": 0},
            },
        },
        ["days", "people"],
    ),
]


# ---------- Argument helpers ----------


def _require_str(arguments: dict, key: str) -> str:
    value = str(arguments.get(key) or "").strip()
    if not value:
        raise ValueError(f"'{key}' is required.")
    return value


def _require_int(arguments: dict, key: str, minimum: int, maximum: int) -> int:
    raw = arguments.get(key)
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise ValueError(f"'{key}' must be a whole number.") from None
    if value < minimum or value > maximum:
        raise ValueError(f"'{key}' must be between {minimum} and {maximum}.")
    return value


def _require_date(arguments: dict, key: str) -> datetime.date:
    raw = _require_str(arguments, key)
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        raise ValueError(f"'{key}' must be a date like 2026-11-20.") from None


def _require_list(arguments: dict, key: str) -> list:
    value = arguments.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"'{key}' must be a non-empty list.")
    return value


# The concession categories the model may ask for.
CONCESSIONS = ("senior_citizen", "army", "student", "doctor", "nurse")


def _optional_concession(arguments: dict) -> str | None:
    """Read the concession category, when the model names a known one."""
    value = arguments.get("concession")
    if not isinstance(value, str):
        return None
    value = value.strip().lower()
    return value if value in CONCESSIONS else None


def _build_request(model, arguments: dict):
    """Build a request model, turning a validation error into a plain message.

    The model knows the rules (a date cannot be in the past, the two places
    must differ). Its error text is long, so the first message is used.
    """
    try:
        return model(**arguments)
    except ValidationError as exc:
        first = exc.errors()[0].get("msg", "The arguments were not valid.") if exc.errors() else "The arguments were not valid."
        raise ValueError(str(first).removeprefix("Value error, ")) from None


# ---------- Tool handlers ----------


def _handle_search_flights(arguments: dict) -> dict:
    """Look up flights between two places."""
    request = _build_request(
        FlightSearchRequest,
        {
            "origin": _require_str(arguments, "origin"),
            "destination": _require_str(arguments, "destination"),
            "date": _require_date(arguments, "date"),
            "passengers": _require_int(arguments, "passengers", 1, 9),
            "concession": _optional_concession(arguments),
        },
    )

    results = search_flights(
        origin=request.origin,
        destination=request.destination,
        date=request.date.isoformat(),
        passengers=request.passengers,
        concession=request.concession,
    )

    return {
        "origin": request.origin,
        "destination": request.destination,
        "date": request.date.isoformat(),
        "is_mock": True,
        "results": [result.model_dump() for result in results],
    }


def _handle_search_hotels(arguments: dict) -> dict:
    """Look up places to stay."""
    request = _build_request(
        HotelSearchRequest,
        {
            "destination": _require_str(arguments, "destination"),
            "check_in": _require_date(arguments, "check_in"),
            "check_out": _require_date(arguments, "check_out"),
            "guests": _require_int(arguments, "guests", 1, 20),
            "concession": _optional_concession(arguments),
        },
    )

    results = search_hotels(
        destination=request.destination,
        check_in=request.check_in.isoformat(),
        check_out=request.check_out.isoformat(),
        guests=request.guests,
        concession=request.concession,
    )

    return {
        "destination": request.destination,
        "check_in": request.check_in.isoformat(),
        "check_out": request.check_out.isoformat(),
        "is_mock": True,
        "results": [result.model_dump() for result in results],
    }


def _handle_search_transport(arguments: dict) -> dict:
    """Look up buses or trains."""
    request = _build_request(
        TransportSearchRequest,
        {
            "origin": _require_str(arguments, "origin"),
            "destination": _require_str(arguments, "destination"),
            "date": _require_date(arguments, "date"),
            "passengers": _require_int(arguments, "passengers", 1, 9),
            "mode": _require_str(arguments, "mode").lower(),
            "concession": _optional_concession(arguments),
        },
    )

    results = search_transport(
        mode=request.mode,
        origin=request.origin,
        destination=request.destination,
        date=request.date.isoformat(),
        passengers=request.passengers,
        concession=request.concession,
    )

    return {
        "origin": request.origin,
        "destination": request.destination,
        "date": request.date.isoformat(),
        "mode": request.mode,
        "is_mock": True,
        "results": [result.model_dump() for result in results],
    }


def _handle_geocode_place(arguments: dict) -> dict:
    """Look up one place on the map."""
    place = _require_str(arguments, "place")

    location = geocode_place(place)
    if location is None:
        return {
            "place": place,
            "found": False,
            "message": "This place could not be found on the map.",
        }

    return {
        "place": place,
        "found": True,
        "name": location.name,
        "display_name": location.display_name,
        "coordinates": location.coordinates.model_dump(),
        "map_url": (
            f"https://www.openstreetmap.org/?q={location.coordinates.lat},"
            f"{location.coordinates.lng}"
        ),
    }


def _handle_suggest_stop_order(arguments: dict) -> dict:
    """Order the places of one day so nearby places are visited together."""
    places = [str(place).strip() for place in _require_list(arguments, "places")]
    places = [place for place in places if place][:MAX_STOPS_PER_CALL]

    if not places:
        raise ValueError("'places' must contain at least one place.")

    stops: list[RouteStop] = []
    unlocated: list[RouteStop] = []

    for index, place in enumerate(places):
        location = geocode_place(place)
        if location is None:
            unlocated.append(
                RouteStop(order=index + 1, name=place, location=place, coordinates=None)
            )
            continue

        stops.append(
            RouteStop(
                order=index + 1,
                name=location.name or place,
                location=place,
                coordinates=location.coordinates,
            )
        )

    # The visit order only reorders the places it could locate. The rest
    # keep their original order and are listed at the end, so no place is
    # ever dropped from the answer.
    ordered = suggest_visit_order(stops) + unlocated

    return {
        "suggested_order": [stop.location for stop in ordered],
        "stops": [
            {
                "order": index + 1,
                "place": stop.location,
                "name": stop.name,
                "coordinates": (
                    stop.coordinates.model_dump() if stop.coordinates else None
                ),
            }
            for index, stop in enumerate(ordered)
        ],
        "missing": [stop.location for stop in unlocated],
    }


def _handle_estimate_trip_cost(arguments: dict) -> dict:
    """Work out the estimated cost of a trip with the budget formulas.

    The activity costs come from the plan, so the estimate moves when the
    plan changes. Nothing here is an AI guess.
    """
    days = _require_int(arguments, "days", 1, 30)
    people = _require_int(arguments, "people", 1, 20)

    raw_costs = arguments.get("activity_costs")
    activity_costs: list[float] = []
    if isinstance(raw_costs, list):
        for value in raw_costs:
            try:
                cost = float(value)
            except (TypeError, ValueError):
                continue
            if cost < 0:
                continue
            activity_costs.append(cost)

    # The budget service reads the costs from a trip, so a throwaway trip
    # is built from the numbers the model gave us.
    activities = [
        Activity(time="09:00", name="Activity", location="Destination", estimated_cost=cost)
        for cost in activity_costs
    ]
    trip = Trip(
        trip_id="budget-estimate",
        destination="Destination",
        days=days,
        people=people,
        budget=1,
        itinerary=[DayPlan(day=1, title="Budget estimate", activities=activities)],
    )

    costs = estimate_budget(trip)

    return {
        "days": days,
        "people": people,
        "is_estimate": True,
        "estimated_costs": costs.model_dump(),
    }


TOOL_HANDLERS: dict[str, Callable[[dict], dict]] = {
    "search_flights": _handle_search_flights,
    "search_hotels": _handle_search_hotels,
    "search_transport": _handle_search_transport,
    "geocode_place": _handle_geocode_place,
    "suggest_stop_order": _handle_suggest_stop_order,
    "estimate_trip_cost": _handle_estimate_trip_cost,
}


# ---------- Calling the tools ----------


def get_tool_definitions() -> list[dict]:
    """The tool definitions to send to the provider.

    A copy is returned, so a caller that edits the list cannot change what
    the next caller sees.
    """
    return copy.deepcopy(TOOL_DEFINITIONS)


def _parse_arguments(raw_arguments: Any) -> dict:
    """Read the arguments of a tool call.

    Providers send the arguments as a JSON string. An empty string means
    the call had no arguments, which is fine for a tool without any.
    """
    if raw_arguments is None:
        return {}
    if isinstance(raw_arguments, dict):
        return raw_arguments
    if isinstance(raw_arguments, str):
        text = raw_arguments.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            raise ValueError("The tool arguments were not valid JSON.") from None
        if not isinstance(parsed, dict):
            raise ValueError("The tool arguments were not a JSON object.")
        return parsed
    raise ValueError("The tool arguments had an unexpected shape.")


def call_tool(name: str, arguments: Any = None) -> dict:
    """Run one tool and return its result.

    Args:
        name: The name of the tool, as the model asked for it.
        arguments: The arguments, either a dict or a JSON string.

    Returns:
        A dict with `ok`. When it is True, `result` holds the tool's
        answer. When it is False, `error` explains what went wrong, so the
        model can try something else. Nothing here raises.
    """
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return {
            "ok": False,
            "error": f"Unknown tool '{name}'.",
            "available_tools": sorted(TOOL_HANDLERS),
        }

    try:
        parsed = _parse_arguments(arguments)
        result = handler(parsed)
    except ValueError as exc:
        # The model asked for something we cannot do. Tell it what to fix.
        logger.info("Tool '%s' was called with bad arguments: %s", name, exc)
        return {"ok": False, "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - a tool must never break a trip
        logger.warning("Tool '%s' failed: %s", name, exc)
        return {
            "ok": False,
            "error": "This tool could not answer right now. Try again or without it.",
        }

    return {"ok": True, "result": result}


def run_tool_calls(tool_calls: list[dict]) -> list[dict]:
    """Run every tool call of one assistant message.

    Args:
        tool_calls: The `tool_calls` list of an assistant message.

    Returns:
        The `tool` messages to send back to the model, in the same order
        as the calls.
    """
    return [build_tool_message(call) for call in tool_calls or []]


def build_assistant_tool_message(tool_calls: list[dict]) -> dict:
    """Build the assistant message that carries the tool calls.

    Some providers need this message in the conversation before the tool
    results, because the tool results refer back to it by id.
    """
    return {
        "role": "assistant",
        "content": None,
        "tool_calls": list(tool_calls or []),
    }


def build_tool_message(tool_call: dict) -> dict:
    """Build the `tool` message for one tool call.

    The content is the tool's answer as JSON, which is what the provider
    expects to read back.
    """
    function = tool_call.get("function") or {}
    name = function.get("name") or ""
    answer = call_tool(name, function.get("arguments"))

    return {
        "role": "tool",
        "tool_call_id": tool_call.get("id") or "",
        "name": name,
        "content": json.dumps(answer, default=str),
    }


# The names the coordinator and the tests use.
__all__ = [
    "TOOL_DEFINITIONS",
    "TOOL_HANDLERS",
    "get_tool_definitions",
    "call_tool",
    "run_tool_calls",
    "build_assistant_tool_message",
    "build_tool_message",
]
