import math
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status, Response
from sqlalchemy import asc, desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.vehicle_data import VehicleData
from app.schemas.vehicle_data import PaginatedVehicleData, SortField, SortOrder, VehicleDataRead
from app.core.config import settings
from app.services.csv_import import import_rows, parse_csv
from app.services.read_cache import TTLCache

from app.services.vehicle_export import (
    ExportFormat,
    build_vehicle_export,
)
 
router = APIRouter(prefix="/api/v1/vehicle_data", tags=["vehicle-data"]) # router allows us to group endpoints together 

read_cache = TTLCache(ttl_seconds=settings.read_cache_ttl_seconds)

SORT_COLUMNS = { # map the ORM object onto the dictionary 
    "id": VehicleData.id,
    "timestamp": VehicleData.timestamp,
    "speed": VehicleData.speed,
    "odometer": VehicleData.odometer,
    "soc": VehicleData.soc,
    "elevation": VehicleData.elevation,
    "shift_state": VehicleData.shift_state,
}


@router.get("/", response_model=PaginatedVehicleData)
def list_vehicle_data(
    vehicle_id: str = Query(min_length=1),
    start_timestamp: datetime | None = None,
    end_timestamp: datetime | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort_by: SortField = "timestamp",
    sort_order: SortOrder = "asc",
    db: Session = Depends(get_db), # access the database connection 
) -> PaginatedVehicleData:
    """
    Add get endpoint to the paginated vehicle data onto the
    router   
    """    
    if start_timestamp and end_timestamp and start_timestamp > end_timestamp: # if we have errors where we have a start datetime that is further into the future thatn the start timestamp 
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_timestamp cannot be later than end_timestamp",
        )

    filters = [VehicleData.vehicle_id == vehicle_id] # only get the list for the vehicle data that matches the vehicle_data input 
    
    if start_timestamp: # append ge than the start_timestamp 
        filters.append(VehicleData.timestamp >= start_timestamp)
        
    if end_timestamp: # append le to the end_timestamp
        filters.append(VehicleData.timestamp <= end_timestamp)

    # Now that we have created the filter for filtering the particular car id, we need to now find
    # the total number of rows that match this criteria 

    cache_key = (
        "list:"
        f"{vehicle_id}:{start_timestamp}:{end_timestamp}:"
        f"{page}:{page_size}:{sort_by}:{sort_order}"
    )

    def read_from_db() -> PaginatedVehicleData:
        total = db.scalar(select(func.count()).select_from(VehicleData).where(*filters)) or 0
        sort_column = SORT_COLUMNS[sort_by] # select the column we want to sort the filtered table by - here we are choosing the timestamp
        ordering = desc(sort_column) if sort_order == "desc" else asc(sort_column) # default is asc

        rows = db.scalars(
            select(VehicleData)
            .where(*filters)
            .order_by(ordering, VehicleData.id.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return PaginatedVehicleData( # return the pydantic object which will check and structure data at runtime using Python type annotations
            items=[VehicleDataRead.model_validate(row) for row in rows],
            page=page,
            page_size=page_size,
            total=total,
            pages=math.ceil(total / page_size) if total else 0,
        )

    return read_cache.get_or_set(cache_key, read_from_db)


@router.get("/{row_id}/", response_model=VehicleDataRead)
def get_vehicle_data(row_id: int, db: Session = Depends(get_db)) -> VehicleDataRead:
    """
    Get just the row number vehicle data 
    """
    def read_from_db() -> VehicleDataRead:
        row = db.get(VehicleData, row_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Vehicle data row not found")
        return VehicleDataRead.model_validate(row)

    return read_cache.get_or_set(f"row:{row_id}", read_from_db)


@router.get(
    "/{vehicle_id}/export",
    status_code=status.HTTP_200_OK,
)
def export_vehicle_data(
    vehicle_id: str,
    export_format: ExportFormat = Query(
        default=ExportFormat.CSV,
        alias="format",
    ),
    db: Session = Depends(get_db),
) -> Response:
    """
    Export all records for one vehicle as JSON, CSV, or Excel.
    """
    query = (
        select(VehicleData)
        .where(VehicleData.vehicle_id == vehicle_id)
        .order_by(VehicleData.timestamp) # extract the dataset that matches the vehicle_id 
    )

    rows = list(db.scalars(query).all()) # create list of the data 

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for vehicle '{vehicle_id}'",
        )

    exported_file = build_vehicle_export(
        rows=rows,
        vehicle_id=vehicle_id,
        export_format=export_format,
    )

    return Response(
        content=exported_file.content,
        media_type=exported_file.media_type,
        headers={
            "Content-Disposition": (
                f'attachment; filename="{exported_file.filename}"'
            )
        },
    )


@router.post("/import", status_code=status.HTTP_201_CREATED) 
async def import_vehicle_csv(
    vehicle_id: str = Query(min_length=1),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    """
    import data from a new csv, returning a HTTP 201 created status 
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="A CSV file is required")

    try:
        rows = parse_csv(await file.read(), vehicle_id) # parse csv to pydantic object 
        inserted, skipped = import_rows(db, rows) # insert into database
        if inserted:
            read_cache.clear()
    except (UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return {"inserted": inserted, "skipped": skipped}
