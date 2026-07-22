import sys
from pathlib import Path

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.csv_import import import_rows, parse_csv, vehicle_id_from_path


def load_directory(directory: Path) -> None:
    """
    Find all files in the /data directory and load in the database 
    """
    Base.metadata.create_all(bind=engine)
    files = sorted(directory.glob("*.csv"))
    if not files:
        raise SystemExit(f"No CSV files found in {directory}")

    with SessionLocal() as db:
        for path in files:
            rows = parse_csv(path.read_bytes(), vehicle_id_from_path(path))
            inserted, skipped = import_rows(db, rows)
            print(f"{path.name}: inserted={inserted}, skipped={skipped}")


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "/data")
    load_directory(target)
