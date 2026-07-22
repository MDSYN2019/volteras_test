import csv
import io
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.vehicle_data import VehicleData
from app.schemas.vehicle_data import VehicleDataCreate

REQUIRED_COLUMNS = {"timestamp", "speed", "odometer", "soc", "elevation", "shift_state"} # columns of the csv 
NULL_VALUES = {"", "NULL", "NONE", "N/A"}

def _is_null(value: str | None) -> bool:
    return value is None or value.strip().upper() in NULL_VALUES


def _nullable_float(value: str | None) -> float | None:
    """
    If we have an empty string, we should return None 
    """
    if _is_null(value):
        return None
    return float(value)

def _nullable_string(value: str | None) -> str | None:
    """
    If we have any of the above NULL_VALUES, then we should cast as None, or
    strip the string value
    """
    if _is_null(value):
        return None
    return value.strip()


def _required_float(value: str | None, column: str) -> float:
    """
    If we have an empty string representation of a float or none,
    return error. Otherwise, cast as float
    """
    if value is None or value.strip() == "":
        raise ValueError(f"{column} cannot be empty")
    return float(value)


def parse_csv(content: bytes, vehicle_id: str) -> list[VehicleDataCreate]:
    """
    Validate the column number and names and append to rows as list of pydantic objects 
    """
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text)) # We get a list of dicts for the csv reader 

    fieldnames = set(reader.fieldnames or [])
    missing = REQUIRED_COLUMNS - fieldnames # ensure that we don't have missing columns 
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    rows: list[VehicleDataCreate] = []
    for row_number, row in enumerate(reader, start=2): # ensure that we start from  
        try:
            rows.append(
                VehicleDataCreate(
                    vehicle_id=vehicle_id,
                    timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                    speed=_nullable_float(row["speed"]),
                    odometer=_required_float(row["odometer"], "odometer"),
                    soc=_required_float(row["soc"], "soc"),
                    elevation=_required_float(row["elevation"], "elevation"),
                    shift_state=_nullable_string(row["shift_state"]),
                )
            )
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid row {row_number}: {exc}") from exc

    return rows


def import_rows(db: Session, rows: list[VehicleDataCreate]) -> tuple[int, int]:
    """
    Add the rows we created with parse_csv to the database 
    """
    inserted = 0
    skipped = 0

    for row in rows:
        exists = db.scalar(
            select(VehicleData.id).where(
                VehicleData.vehicle_id == row.vehicle_id,
                VehicleData.timestamp == row.timestamp,
            )
        )
        # if exists, then we don't need to add in duplicate entries  
        if exists is not None:
            skipped += 1
            continue
        
        # otherewise, cast into the ORM and subsequently to postgres 
        db.add(VehicleData(**row.model_dump()))
        inserted += 1
 
    db.commit() # commit to the database 
    return inserted, skipped

def vehicle_id_from_path(path: Path) -> str:
    vehicle_id = path.stem.strip()
    if not vehicle_id:
        raise ValueError("CSV filename must contain a vehicle id")
    return vehicle_id
