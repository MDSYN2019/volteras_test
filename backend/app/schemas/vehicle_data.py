from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SortField = Literal["id", "timestamp", "speed", "odometer", "soc", "elevation", "shift_state"]
SortOrder = Literal["asc", "desc"]


class VehicleDataRead(BaseModel):
    """
    Pydantic model to ensure type-casting when we read in the vehicle data csvs 
    """
    model_config = ConfigDict(from_attributes=True) # allow building from an ORM object 
    id: int
    vehicle_id: str
    timestamp: datetime
    speed: float | None
    odometer: float
    soc: float
    elevation: float
    shift_state: str | None


class PaginatedVehicleData(BaseModel):
    """
    Pydantic model to ensure type-casting   
    """
    items: list[VehicleDataRead]
    page: int
    page_size: int
    total: int
    pages: int


class VehicleDataCreate(BaseModel):
    """
    Pydantic model to ensure type-casting 
    """
    vehicle_id: str = Field(min_length=1, max_length=100)
    timestamp: datetime
    speed: float | None = None
    odometer: float = Field(ge=0)
    soc: float = Field(ge=0, le=100)
    elevation: float
    shift_state: str | None = Field(default=None, max_length=1)

    @field_validator("shift_state")
    @classmethod
    def normalise_shift_state(cls, value: str | None) -> str | None:
        if value is None or value.strip() == "":
            return None
        return value.strip().upper()
