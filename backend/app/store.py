"""Trip storage module with database persistence.

Date: 20-10-2026 — Migrated from in-memory to SQLite database persistence.
Maintains backwards compatibility with in-memory cache for transition period.
"""
from typing import Dict
import logging

from .models.trip import Trip

# Configure logging
logger = logging.getLogger(__name__)

# In-memory cache for backwards compatibility
TRIPS: Dict[str, Trip] = {}

# Database functions (lazy import to avoid circular dependencies)
_db_initialized = False

def _get_db():
    """Lazy-load database module to avoid import issues."""
    global _db_initialized
    try:
        from .database import db, init_db
        if not _db_initialized:
            init_db()
            _db_initialized = True
        return db
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return None


def generate_trip_id() -> str:
    """Generate a unique trip ID."""
    import uuid
    return str(uuid.uuid4())


def save_trip(trip_id: str, trip_data: dict) -> bool:
    """Save a trip to the database.

    Returns True if saved successfully, False otherwise.
    Never reports success if the database operation fails.

    Date: 20-10-2026 — Database persistence with proper error handling
    """
    db = _get_db()
    if db is None:
        logger.warning("Database unavailable, using in-memory fallback")
        # Fall back to in-memory storage
        from .models.trip import Trip as TripModel
        TRIPS[trip_id] = TripModel(**trip_data) if isinstance(trip_data, dict) else trip_data
        return False  # Never report success if database fails

    try:
        db.save_trip(trip_id, trip_data)
        # Update in-memory cache
        from .models.trip import Trip as TripModel
        TRIPS[trip_id] = TripModel(**trip_data) if isinstance(trip_data, dict) else trip_data
        return True
    except Exception as e:
        logger.error(f"Failed to save trip {trip_id}: {e}")
        return False


def get_trip(trip_id: str) -> dict | None:
    """Get a trip from the database or cache.

    Returns trip data dict or None if not found.
    """
    db = _get_db()
    if db is None:
        # Fall back to in-memory cache
        trip = TRIPS.get(trip_id)
        return trip.model_dump() if trip else None

    try:
        trip_data = db.get_trip(trip_id)
        if trip_data:
            # Update in-memory cache
            from .models.trip import Trip as TripModel
            TRIPS[trip_id] = TripModel(**trip_data)
        return trip_data
    except Exception as e:
        logger.error(f"Failed to get trip {trip_id}: {e}")
        # Fall back to in-memory cache
        trip = TRIPS.get(trip_id)
        return trip.model_dump() if trip else None


def delete_trip(trip_id: str) -> bool:
    """Delete a trip from the database and cache.

    Returns True if deleted, False if not found or error occurred.
    """
    db = _get_db()
    if db is None:
        # Fall back to in-memory cache
        if trip_id in TRIPS:
            del TRIPS[trip_id]
            return True
        return False

    try:
        deleted = db.delete_trip(trip_id)
        if deleted and trip_id in TRIPS:
            del TRIPS[trip_id]
        return deleted
    except Exception as e:
        logger.error(f"Failed to delete trip {trip_id}: {e}")
        return False