"""SQLite database module for trip persistence.

This module provides a simple SQLite-based storage layer for trips.
For MVP, this replaces the in-memory store. In production, this could
be replaced with PostgreSQL or another server database.
"""
import json
import os
import sqlite3
from datetime import date
from pathlib import Path
from typing import Any

from app.config import APP_ENV

# Database file location. TRIP_DB_PATH lets the test suite use its own file
# instead of filling the real database with test trips.
DB_DIR = Path(__file__).parent.parent / "data"
DB_PATH = Path(os.getenv("TRIP_DB_PATH") or (DB_DIR / "trips.db"))


def get_db_connection() -> sqlite3.Connection:
    """Create and return a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database with the trips table.

    Creates the data directory and trips table if they don't exist.
    Safe to call multiple times (idempotent).
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trips (
            trip_id TEXT PRIMARY KEY,
            data TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def trip_to_json(trip: dict[str, Any]) -> str:
    """Convert a trip dict to JSON string for storage.

    Handles date objects by converting them to ISO format strings.
    """
    trip_copy = trip.copy()

    # Convert date objects to strings
    if "travel_date" in trip_copy and isinstance(trip_copy["travel_date"], date):
        trip_copy["travel_date"] = trip_copy["travel_date"].isoformat()

    # Convert itinerary objects
    if "itinerary" in trip_copy:
        itinerary_copy = []
        for day in trip_copy["itinerary"]:
            day_copy = day.copy()
            if "activities" in day_copy:
                day_copy["activities"] = [
                    {
                        **a,
                        "estimated_cost": (
                            float(a["estimated_cost"])
                            if a.get("estimated_cost") is not None
                            else None
                        ),
                    }
                    for a in day_copy["activities"]
                ]
            itinerary_copy.append(day_copy)
        trip_copy["itinerary"] = itinerary_copy

    # Convert estimated_costs
    if "estimated_costs" in trip_copy and trip_copy["estimated_costs"]:
        costs = trip_copy["estimated_costs"]
        trip_copy["estimated_costs"] = {
            k: float(v) if v is not None else None
            for k, v in costs.items()
        }

    return json.dumps(trip_copy)


def json_to_trip(json_str: str) -> dict[str, Any]:
    """Convert JSON string from database back to trip dict.

    Converts ISO format date strings back to date objects.
    """
    data = json.loads(json_str)

    # Convert travel_date back to date object
    if "travel_date" in data and data["travel_date"]:
        try:
            data["travel_date"] = date.fromisoformat(data["travel_date"])
        except (ValueError, TypeError):
            pass  # Keep as-is if not a valid date string

    return data


# Date: 20-10-2026 — SQLite database persistence for trips
# Replaces in-memory store for production-ready persistence
class TripDatabase:
    """Database wrapper for trip CRUD operations."""

    def __init__(self):
        init_db()
        self._connected = True

    def _ensure_connected(self) -> None:
        """Raise if database is not connected."""
        if not self._connected:
            raise RuntimeError("Database connection lost")

    def save_trip(self, trip_id: str, trip_data: dict[str, Any]) -> None:
        """Save or update a trip in the database.

        Args:
            trip_id: Unique identifier for the trip
            trip_data: Full trip dictionary to store

        Raises:
            RuntimeError: If database connection is lost
        """
        self._ensure_connected()

        conn = get_db_connection()
        cursor = conn.cursor()

        now = date.today().isoformat()
        json_data = trip_to_json(trip_data)

        cursor.execute(
            """
            INSERT OR REPLACE INTO trips (trip_id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            """,
            (trip_id, json_data, now, now),
        )

        conn.commit()
        conn.close()

    def get_trip(self, trip_id: str) -> dict[str, Any] | None:
        """Retrieve a trip from the database.

        Args:
            trip_id: Unique identifier for the trip

        Returns:
            Trip dictionary or None if not found

        Raises:
            RuntimeError: If database connection is lost
        """
        self._ensure_connected()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM trips WHERE trip_id = ?", (trip_id,))
        row = cursor.fetchone()

        conn.close()

        if row:
            return json_to_trip(row["data"])
        return None

    def delete_trip(self, trip_id: str) -> bool:
        """Delete a trip from the database.

        Args:
            trip_id: Unique identifier for the trip

        Returns:
            True if trip was deleted, False if not found

        Raises:
            RuntimeError: If database connection is lost
        """
        self._ensure_connected()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM trips WHERE trip_id = ?", (trip_id,))
        deleted = cursor.rowcount > 0

        conn.commit()
        conn.close()

        return deleted

    def list_trips(self) -> list[dict[str, Any]]:
        """List all trips in the database.

        Returns:
            List of trip dictionaries

        Raises:
            RuntimeError: If database connection is lost
        """
        self._ensure_connected()

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT data FROM trips ORDER BY updated_at DESC")
        rows = cursor.fetchall()

        conn.close()

        return [json_to_trip(row["data"]) for row in rows]


# Global database instance
# This replaces the in-memory TRIPS dict for production use
db = TripDatabase()


# For backwards compatibility during migration
# The store.py module will delegate to this database
def save_trip(trip_id: str, trip_data: dict[str, Any]) -> None:
    """Convenience function to save a trip."""
    db.save_trip(trip_id, trip_data)


def get_trip(trip_id: str) -> dict[str, Any] | None:
    """Convenience function to get a trip."""
    return db.get_trip(trip_id)


def delete_trip(trip_id: str) -> bool:
    """Convenience function to delete a trip."""
    return db.delete_trip(trip_id)
