from datetime import date
from typing import Annotated

from pydantic import StringConstraints

# A place name: spaces at both ends are removed, then 2 to 80 characters are required.
Place = Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]


def not_in_past(value: date) -> date:
    """Rejects dates before today (server date)."""
    if value < date.today():
        raise ValueError("Choose today or a later date.")
    return value


def different_places(origin: str | None, destination: str) -> str:
    """Rejects the same place for 'from' and 'to'. Skipped if origin was already invalid."""
    if origin and origin.lower() == destination.lower():
        raise ValueError("Choose a different place from where you are travelling from.")
    return destination
