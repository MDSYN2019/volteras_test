from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings # import the environmental variables

# the database url here should be the address of your docker compose version of postgres
# e.g.  DATABASE_URL=postgresql+psycopg://postgres:password@db:5432/my_database 
engine = create_engine(settings.database_url, pool_pre_ping=True)

# create a local session to postgres
SessionLocal = sessionmaker(bind=engine, 
                            autoflush=False,
                            expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """
    Create a database session and yield the db session to fastapi,
    and ensure closing of the session 
    """
    db = SessionLocal()
    try:
        yield db 
    finally: # ensure that the connection to the database closes after we end a session 
        db.close() 
