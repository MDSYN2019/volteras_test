import csv
import io
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from openpyxl import Workbook

from app.models.vehicle_data import VehicleData


class ExportFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    XLSX = "xlsx"


EXPORT_COLUMNS = (
    "vehicle_id",
    "timestamp",
    "speed",
    "odometer",
    "soc",
    "elevation",
    "shift_state",
)


@dataclass(frozen=True) # ensure this is immutable 
class ExportedFile:
    content: bytes
    filename: str
    media_type: str


def _safe_filename(value: str) -> str:
    """
    Prevent unusual characters from appearing in the filenames 
    """
    cleaned = re.sub(r"[^a-zA-Z0-9_.-]", "_", value)
    return cleaned or "vehicle"


def _vehicle_data_to_record(row: VehicleData) -> dict[str, Any]:
    """
    Convert the SQLAlchemy VehicledData pydantic object into a dict 
    """
    return {
        "vehicle_id": row.vehicle_id,
        "timestamp": row.timestamp.isoformat(),
        "speed": row.speed,
        "odometer": row.odometer,
        "soc": row.soc,
        "elevation": row.elevation,
        "shift_state": row.shift_state,
    }


def _build_json(records: list[dict[str, Any]]) -> bytes:
    """
    Build json format 
    """
    return json.dumps(
        records,
        ensure_ascii=False,
        indent=2,
    ).encode("utf-8")


def _build_csv(records: list[dict[str, Any]]) -> bytes:
    """
    Build csv format
    """
    output = io.StringIO(newline="")

    writer = csv.DictWriter(
        output,
        fieldnames=EXPORT_COLUMNS,
    )

    writer.writeheader()
    writer.writerows(records)

    return output.getvalue().encode("utf-8-sig")


def _build_excel(records: list[dict[str, Any]]) -> bytes:
    """
    Build excel format 
    """
    output = io.BytesIO()

    # write_only mode is more memory-efficient for generated spreadsheets.
    workbook = Workbook(write_only=True)
    worksheet = workbook.create_sheet(title="Vehicle data")

    worksheet.append(list(EXPORT_COLUMNS))

    for record in records:
        worksheet.append(
            [record[column] for column in EXPORT_COLUMNS]
        )

    workbook.save(output)

    return output.getvalue()


def build_vehicle_export(
    rows: list[VehicleData],
    vehicle_id: str,
    export_format: ExportFormat,
) -> ExportedFile:
    records = [_vehicle_data_to_record(row) for row in rows]
    safe_vehicle_id = _safe_filename(vehicle_id)

    if export_format == ExportFormat.JSON:
        return ExportedFile(
            content=_build_json(records),
            filename=f"{safe_vehicle_id}_vehicle_data.json",
            media_type="application/json",
        )

    if export_format == ExportFormat.CSV:
        return ExportedFile(
            content=_build_csv(records),
            filename=f"{safe_vehicle_id}_vehicle_data.csv",
            media_type="text/csv; charset=utf-8",
        )

    return ExportedFile(
        content=_build_excel(records),
        filename=f"{safe_vehicle_id}_vehicle_data.xlsx",
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )
