"""Shared location event creation and validation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


def location_event(vehicle_id: str, latitude: float, longitude: float, sequence: int) -> dict:
    """Create the versioned event sent by a vehicle producer."""
    return {
        "schema_version": 1,
        "vehicle_id": vehicle_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "latitude": latitude,
        "longitude": longitude,
        "sequence": sequence,
    }


def validate_and_enrich(value: Any) -> dict:
    """Validate a raw event and create the dashboard data product."""
    if not isinstance(value, dict):
        raise ValueError("event must be an object")
    required = {"schema_version", "vehicle_id", "timestamp", "latitude", "longitude", "sequence"}
    missing = required - value.keys()
    if missing:
        raise ValueError(f"missing fields: {', '.join(sorted(missing))}")
    latitude = float(value["latitude"])
    longitude = float(value["longitude"])
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not str(value["vehicle_id"]).strip():
        raise ValueError("vehicle_id must not be empty")
    datetime.fromisoformat(str(value["timestamp"]).replace("Z", "+00:00"))
    return {
        **value,
        "latitude": latitude,
        "longitude": longitude,
        "processed_at": datetime.now(UTC).isoformat(),
        "product": "live_vehicle_location",
    }

