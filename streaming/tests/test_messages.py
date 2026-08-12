from datetime import UTC, datetime

import pytest

from kafka_pipeline.messages import location_event, validate_and_enrich


def test_location_product_is_validated_and_enriched() -> None:
    raw = location_event("car-7", 51.5, -0.12, 4)
    product = validate_and_enrich(raw)
    assert product["product"] == "live_vehicle_location"
    assert product["vehicle_id"] == "car-7"
    assert datetime.fromisoformat(product["processed_at"]).tzinfo == UTC


@pytest.mark.parametrize(
    ("field", "value"), [("latitude", 91), ("latitude", -91), ("longitude", 181)]
)
def test_invalid_coordinates_are_rejected(field: str, value: float) -> None:
    raw = location_event("car-7", 51.5, -0.12, 4)
    raw[field] = value
    with pytest.raises(ValueError):
        validate_and_enrich(raw)
