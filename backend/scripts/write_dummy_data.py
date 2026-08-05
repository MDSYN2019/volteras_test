from __future__ import annotations

import os
import random
import time
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.exc import IntegrityError

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models.vehicle_data import VehicleData

VEHICLE_IDS = os.getenv("DUMMY_VEHICLE_IDS", "demo-car-1,demo-car-2").split(",")
INTERVAL_SECONDS = int(os.getenv("DUMMY_WRITE_INTERVAL_SECONDS", "10"))
BATCH_SIZE = int(os.getenv("DUMMY_WRITE_BATCH_SIZE", "5"))


def build_row(vehicle_id: str, timestamp: datetime) -> VehicleData:
    return VehicleData(
        vehicle_id=vehicle_id,
        timestamp=timestamp,
        speed=round(random.uniform(0, 80), 2),
        odometer=round(10_000 + random.uniform(0, 500), 2),
        soc=round(random.uniform(20, 95), 2),
        elevation=round(random.uniform(0, 250), 2),
        shift_state=random.choice(["D", "P", "R", None]),
    )


def write_batch() -> int:
    inserted = 0
    now = datetime.now(UTC).replace(microsecond=0)
    with SessionLocal() as db:
        for index in range(BATCH_SIZE):
            vehicle_id = random.choice([value.strip() for value in VEHICLE_IDS if value.strip()])
            row = build_row(vehicle_id or f"demo-{uuid.uuid4()}", now + timedelta(seconds=index))
            db.add(row)
            try:
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()
        return inserted


def main() -> None:
    Base.metadata.create_all(bind=engine)
    while True:
        inserted = write_batch()
        print(f"Inserted {inserted} dummy telemetry rows", flush=True)
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
