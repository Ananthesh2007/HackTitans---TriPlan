"""Applies the search filters to a list of results.

The frontend also filters and sorts the results it gets back, so that the
page behaves the same when it runs on the built-in sample data. The rules
here and in `frontend/src/utils/filters.js` are the same rules, written
twice on purpose: the backend has no JavaScript, and the frontend has no
Python.

The rules
---------
- A filter that is left at its default ("any", `None`, `False`) never
  removes a result.
- A result that does not say which concessions it offers is kept for every
  concession, because the provider did not say it was excluded. A live
  provider that does know sends the list of concessions it offers.
- Sorting never changes which results are returned, only their order.
"""

import re
from typing import Any, Iterable

from app.models.search import SearchFilters

# The time windows a traveller can pick, in the order they appear in the day.
DEPARTURE_WINDOWS = {
    "night": (0, 6),
    "morning": (6, 12),
    "afternoon": (12, 18),
    "evening": (18, 24),
}

_NON_AC = re.compile(r"non[\s\-_]*ac", re.IGNORECASE)
_AC = re.compile(r"(^|[^a-z])ac($|[^a-z])", re.IGNORECASE)


def _time_minutes(value: Any) -> int | None:
    """Minutes after midnight for an "HH:MM" string, or None."""
    if not isinstance(value, str):
        return None
    match = re.match(r"^(\d{1,2}):(\d{2})", value.strip())
    if not match:
        return None
    hours, minutes = int(match.group(1)), int(match.group(2))
    if hours > 23 or minutes > 59:
        return None
    return hours * 60 + minutes


def _in_window(value: Any, window: str) -> bool:
    """True when a time falls in the chosen window."""
    minutes = _time_minutes(value)
    if minutes is None:
        return True  # No time to go by, so the result stays.
    start, end = DEPARTURE_WINDOWS[window]
    return start * 60 <= minutes < end * 60


def _price_of(result: dict) -> float | None:
    """The price of a result, whichever field holds it."""
    for key in ("price", "price_per_night"):
        value = result.get(key)
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _has_ac(vehicle_type: Any) -> bool | None:
    """True for AC, False for non-AC, None when the type does not say."""
    if not isinstance(vehicle_type, str):
        return None
    if _NON_AC.search(vehicle_type):
        return False
    if _AC.search(vehicle_type):
        return True
    return None


def _matches_vehicle_filters(result: dict, filters) -> bool:
    """True when a bus or train matches the AC and seat class filters."""
    vehicle_type = result.get("vehicle_type")

    if filters.ac != "any":
        has_ac = _has_ac(vehicle_type)
        if has_ac is not None and has_ac != (filters.ac == "ac"):
            return False

    if filters.seat_class != "any":
        if isinstance(vehicle_type, str):
            wanted = filters.seat_class
            if wanted not in vehicle_type.lower():
                return False

    if filters.tracking and not result.get("tracking"):
        return False

    if filters.is_new and not result.get("is_new"):
        return False

    return True


def _matches_concession(result: dict, concession: str | None) -> bool:
    """True when a result can be booked with the chosen concession."""
    if not concession:
        return True
    offered = result.get("concessions")
    if not isinstance(offered, list) or not offered:
        return True  # The provider did not say, so it is not excluded.
    return concession in offered


def _matches_price(result: dict, filters) -> bool:
    """True when the price is inside the chosen range."""
    price = _price_of(result)
    if price is None:
        return True  # No price, so the range does not exclude it.
    if filters.price_min is not None and price < filters.price_min:
        return False
    if filters.price_max is not None and price > filters.price_max:
        return False
    return True


def apply_filters(results: Iterable[Any], filters, concession: str | None = None) -> list[Any]:
    """Keep only the results that match the filters.

    Args:
        results: The results from a search.
        filters: A `SearchFilters` model, or None.
        concession: The concession the traveller picked, if any.

    Returns:
        A new list with the matching results. The order is the order the
        provider sent them in.
    """
    items = list(results)
    if filters is None and not concession:
        return items

    # The filters are optional, so a search with only a concession still
    # works. The defaults mean "keep everything".
    if filters is None:
        filters = SearchFilters()

    kept = []
    for item in items:
        result = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        if not _matches_concession(result, concession):
            continue
        if not _matches_price(result, filters):
            continue
        if not _matches_vehicle_filters(result, filters):
            continue
        if filters.departure_window != "any" and not _in_window(
            result.get("departure_time") or result.get("check_in_time"),
            filters.departure_window,
        ):
            continue
        kept.append(item)

    return kept


def _duration_minutes(result: dict) -> float | None:
    """The length of a trip from a "9h 50m" style string."""
    duration = result.get("duration")
    if not isinstance(duration, str):
        return None
    hours = re.search(r"(\d+)\s*h", duration)
    minutes = re.search(r"(\d+)\s*m", duration)
    if not hours and not minutes:
        return None
    total = 0.0
    if hours:
        total += int(hours.group(1)) * 60
    if minutes:
        total += int(minutes.group(1))
    return total


def _sort_key(result: dict, sort: str):
    """The key one result is sorted by."""
    price = _price_of(result)
    departure = _time_minutes(result.get("departure_time"))
    duration = _duration_minutes(result)

    if sort == "price_asc":
        return (price is None, price if price is not None else 0)
    if sort == "price_desc":
        return (price is None, -(price if price is not None else 0))
    if sort == "departure_asc":
        return (departure is None, departure if departure is not None else 0)
    if sort == "departure_desc":
        return (departure is None, -(departure if departure is not None else 0))
    if sort == "duration_asc":
        return (duration is None, duration if duration is not None else 0)
    if sort == "name_asc":
        name = result.get("name") or result.get("operator") or result.get("airline") or ""
        return (str(name).lower(),)
    return ()


def sort_results(results: Iterable[Any], sort: str) -> list[Any]:
    """Sort the results the way the user asked for.

    Args:
        results: The results from a search.
        sort: One of the sort keys from `SearchFilters.sort`.

    Returns:
        A new list in the chosen order. The original order is kept for the
        default "recommended" sort, and for results the provider did not give
        enough information about.
    """
    items = list(results)
    if not sort or sort == "recommended":
        return items

    def key_for(item):
        result = item.model_dump() if hasattr(item, "model_dump") else dict(item)
        return _sort_key(result, sort)

    return sorted(items, key=key_for)
