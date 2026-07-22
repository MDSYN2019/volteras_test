from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class VehicleData(Base):
    """
    Create a ORM object that can hold the columns within the CSVs that has been loaded, and cast to
    the appopriate data types for each column
    """
    __tablename__ = "vehicle_data"
    __table_args__ = (
        UniqueConstraint("vehicle_id", "timestamp", name="uq_vehicle_timestamp"), # Create a unique constraint from the permutations of vehicle_id and timestamp 
        Index("ix_vehicle_data_vehicle_timestamp", "vehicle_id", "timestamp"), # Create index 
    )

    id: Mapped[int] = mapped_column(Integer,
                                    primary_key=True,
                                    autoincrement=True)
    
    vehicle_id: Mapped[str] = mapped_column(String(100),
                                            nullable=False,
                                            index=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                nullable=False,
                                                index=True)
    
    speed: Mapped[float | None] = mapped_column(Float,
                                                nullable=True)
    
    odometer: Mapped[float] = mapped_column(Float,
                                            nullable=False)
    
    soc: Mapped[float] = mapped_column(Float,
                                       nullable=False)
    
    elevation: Mapped[float] = mapped_column(Float,
                                             nullable=False)
    
    shift_state: Mapped[str | None] = mapped_column(String(1),
                                                    nullable=True)
