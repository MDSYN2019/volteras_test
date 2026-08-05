from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.vehicle_data import router as vehicle_data_router
from app.db.base import Base
from app.db.session import engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Volteras Vehicle Data API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vehicle_data_router) # add the vehicle router to the main app 



@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight health response for the load balancer."""
    return {"status": "ok"}
