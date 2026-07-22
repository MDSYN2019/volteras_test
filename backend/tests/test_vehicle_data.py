import csv
import io
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import vehicle_data as vehicle_data_api
from app.api.vehicle_data import router
from app.db.session import get_db
from app.models.vehicle_data import VehicleData


def make_vehicle_row(
    row_id: int = 1,
    vehicle_id: str = "car-1",
    timestamp: datetime | None = None,
    speed: float | None = 45.5,
) -> VehicleData:
    """
    Create an unpersisted VehicleData ORM object for endpoint tests.
    """
    row = VehicleData(
        vehicle_id=vehicle_id,
        timestamp=timestamp
        or datetime(2026, 7, 21, 10, 30, tzinfo=timezone.utc),
        speed=speed,
        odometer=12000.25,
        soc=82.0,
        elevation=35.2,
        shift_state="D",
    )
    row.id = row_id
    return row


@pytest.fixture
def db() -> MagicMock:
    return MagicMock(spec=Session)


@pytest.fixture
def client(db: MagicMock):
    """
    Create an isolated FastAPI application containing only this router.

    The real database dependency is replaced with a mocked SQLAlchemy
    session.
    """
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_list_vehicle_data_returns_paginated_rows(
    client: TestClient,
    db: MagicMock,
):
    rows = [
        make_vehicle_row(
            row_id=1,
            timestamp=datetime(
                2026,
                7,
                21,
                10,
                30,
                tzinfo=timezone.utc,
            ),
        ),
        make_vehicle_row(
            row_id=2,
            timestamp=datetime(
                2026,
                7,
                21,
                10,
                31,
                tzinfo=timezone.utc,
            ),
            speed=48.0,
        ),
    ]

    db.scalar.return_value = 3
    db.scalars.return_value.all.return_value = rows

    response = client.get(
        "/api/v1/vehicle_data/",
        params={
            "vehicle_id": "car-1",
            "page": 1,
            "page_size": 2,
            "sort_by": "timestamp",
            "sort_order": "asc",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["page"] == 1
    assert body["page_size"] == 2
    assert body["total"] == 3
    assert body["pages"] == 2
    assert len(body["items"]) == 2

    assert body["items"][0]["id"] == 1
    assert body["items"][0]["vehicle_id"] == "car-1"
    assert body["items"][0]["speed"] == 45.5

    assert body["items"][1]["id"] == 2
    assert body["items"][1]["speed"] == 48.0

    db.scalar.assert_called_once()
    db.scalars.assert_called_once()


def test_list_vehicle_data_returns_empty_page(
    client: TestClient,
    db: MagicMock,
):
    db.scalar.return_value = None
    db.scalars.return_value.all.return_value = []

    response = client.get(
        "/api/v1/vehicle_data/",
        params={"vehicle_id": "car-with-no-data"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "page": 1,
        "page_size": 50,
        "total": 0,
        "pages": 0,
    }


def test_list_vehicle_data_accepts_timestamp_filters(
    client: TestClient,
    db: MagicMock,
):
    db.scalar.return_value = 1
    db.scalars.return_value.all.return_value = [
        make_vehicle_row()
    ]

    response = client.get(
        "/api/v1/vehicle_data/",
        params={
            "vehicle_id": "car-1",
            "start_timestamp": "2026-07-21T10:00:00Z",
            "end_timestamp": "2026-07-21T11:00:00Z",
            "sort_order": "desc",
        },
    )

    assert response.status_code == 200
    assert response.json()["total"] == 1

    db.scalar.assert_called_once()
    db.scalars.assert_called_once()


def test_list_vehicle_data_rejects_reversed_timestamp_range(
    client: TestClient,
    db: MagicMock,
):
    response = client.get(
        "/api/v1/vehicle_data/",
        params={
            "vehicle_id": "car-1",
            "start_timestamp": "2026-07-22T10:00:00Z",
            "end_timestamp": "2026-07-21T10:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": (
            "start_timestamp cannot be later than end_timestamp"
        )
    }

    db.scalar.assert_not_called()
    db.scalars.assert_not_called()


@pytest.mark.parametrize(
    "params",
    [
        {"vehicle_id": ""},
        {"vehicle_id": "car-1", "page": 0},
        {"vehicle_id": "car-1", "page_size": 0},
        {"vehicle_id": "car-1", "page_size": 501},
        {"vehicle_id": "car-1", "sort_by": "unknown"},
        {"vehicle_id": "car-1", "sort_order": "unknown"},
    ],
)
def test_list_vehicle_data_rejects_invalid_query_parameters(
    client: TestClient,
    params: dict[str, str | int],
):
    response = client.get(
        "/api/v1/vehicle_data/",
        params=params,
    )

    assert response.status_code == 422


def test_get_vehicle_data_returns_row(
    client: TestClient,
    db: MagicMock,
):
    db.get.return_value = make_vehicle_row(row_id=42)

    response = client.get("/api/v1/vehicle_data/42/")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == 42
    assert body["vehicle_id"] == "car-1"
    assert body["speed"] == 45.5
    assert body["odometer"] == 12000.25

    db.get.assert_called_once_with(VehicleData, 42)


def test_get_vehicle_data_returns_404_when_missing(
    client: TestClient,
    db: MagicMock,
):
    db.get.return_value = None

    response = client.get("/api/v1/vehicle_data/999/")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Vehicle data row not found"
    }

    db.get.assert_called_once_with(VehicleData, 999)


@pytest.mark.parametrize(
    ("export_format", "extension", "expected_content_type"),
    [
        (
            "json",
            "json",
            "application/json",
        ),
        (
            "csv",
            "csv",
            "text/csv",
        ),
        (
            "xlsx",
            "xlsx",
            (
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
        ),
    ],
)
def test_export_vehicle_data_returns_download(
    client: TestClient,
    db: MagicMock,
    export_format: str,
    extension: str,
    expected_content_type: str,
):
    db.scalars.return_value.all.return_value = [
        make_vehicle_row()
    ]

    response = client.get(
        "/api/v1/vehicle_data/car-1/export",
        params={"format": export_format},
    )

    assert response.status_code == 200

    assert response.headers["content-type"].startswith(
        expected_content_type
    )

    assert response.headers["content-disposition"] == (
        f'attachment; filename="car-1_vehicle_data.{extension}"'
    )

    assert response.content


def test_export_vehicle_data_returns_correct_json(
    client: TestClient,
    db: MagicMock,
):
    db.scalars.return_value.all.return_value = [
        make_vehicle_row()
    ]

    response = client.get(
        "/api/v1/vehicle_data/car-1/export",
        params={"format": "json"},
    )

    assert response.status_code == 200

    records = response.json()

    assert len(records) == 1
    assert records[0]["vehicle_id"] == "car-1"
    assert records[0]["speed"] == 45.5
    assert records[0]["odometer"] == 12000.25
    assert records[0]["shift_state"] == "D"


def test_export_vehicle_data_returns_correct_csv(
    client: TestClient,
    db: MagicMock,
):
    db.scalars.return_value.all.return_value = [
        make_vehicle_row()
    ]

    response = client.get(
        "/api/v1/vehicle_data/car-1/export",
        params={"format": "csv"},
    )

    assert response.status_code == 200

    text = response.content.decode("utf-8-sig")
    records = list(csv.DictReader(io.StringIO(text)))

    assert len(records) == 1
    assert records[0]["vehicle_id"] == "car-1"
    assert records[0]["speed"] == "45.5"
    assert records[0]["odometer"] == "12000.25"


def test_export_vehicle_data_returns_xlsx_file(
    client: TestClient,
    db: MagicMock,
):
    db.scalars.return_value.all.return_value = [
        make_vehicle_row()
    ]

    response = client.get(
        "/api/v1/vehicle_data/car-1/export",
        params={"format": "xlsx"},
    )

    assert response.status_code == 200

    # XLSX files are ZIP archives and begin with the ZIP magic bytes.
    assert response.content.startswith(b"PK")


def test_export_vehicle_data_returns_404_when_no_rows_exist(
    client: TestClient,
    db: MagicMock,
):
    db.scalars.return_value.all.return_value = []

    response = client.get(
        "/api/v1/vehicle_data/missing-car/export",
        params={"format": "csv"},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "No data found for vehicle 'missing-car'"
    }


def test_export_vehicle_data_rejects_unknown_format(
    client: TestClient,
    db: MagicMock,
):
    response = client.get(
        "/api/v1/vehicle_data/car-1/export",
        params={"format": "pdf"},
    )

    assert response.status_code == 422

    db.scalars.assert_not_called()


def test_import_vehicle_csv_returns_inserted_and_skipped_counts(
    client: TestClient,
    db: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
):
    parsed_rows = [MagicMock(), MagicMock(), MagicMock()]

    parse_csv_mock = MagicMock(return_value=parsed_rows)
    import_rows_mock = MagicMock(return_value=(2, 1))

    monkeypatch.setattr(
        vehicle_data_api,
        "parse_csv",
        parse_csv_mock,
    )
    monkeypatch.setattr(
        vehicle_data_api,
        "import_rows",
        import_rows_mock,
    )

    csv_content = (
        b"timestamp,speed,odometer,soc,elevation,shift_state\n"
        b"2026-07-21T10:30:00Z,45,12000,82,35,D\n"
    )

    response = client.post(
        "/api/v1/vehicle_data/import",
        params={"vehicle_id": "car-1"},
        files={
            "file": (
                "vehicle-data.csv",
                csv_content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "inserted": 2,
        "skipped": 1,
    }

    parse_csv_mock.assert_called_once_with(
        csv_content,
        "car-1",
    )
    import_rows_mock.assert_called_once_with(
        db,
        parsed_rows,
    )


def test_import_vehicle_csv_rejects_non_csv_file(
    client: TestClient,
    db: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
):
    parse_csv_mock = MagicMock()
    import_rows_mock = MagicMock()

    monkeypatch.setattr(
        vehicle_data_api,
        "parse_csv",
        parse_csv_mock,
    )
    monkeypatch.setattr(
        vehicle_data_api,
        "import_rows",
        import_rows_mock,
    )

    response = client.post(
        "/api/v1/vehicle_data/import",
        params={"vehicle_id": "car-1"},
        files={
            "file": (
                "vehicle-data.txt",
                b"not a csv",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "A CSV file is required"
    }

    parse_csv_mock.assert_not_called()
    import_rows_mock.assert_not_called()
    db.add.assert_not_called()


def test_import_vehicle_csv_converts_parse_error_to_422(
    client: TestClient,
    db: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
):
    parse_csv_mock = MagicMock(
        side_effect=ValueError(
            "Missing required columns: elevation"
        )
    )
    import_rows_mock = MagicMock()

    monkeypatch.setattr(
        vehicle_data_api,
        "parse_csv",
        parse_csv_mock,
    )
    monkeypatch.setattr(
        vehicle_data_api,
        "import_rows",
        import_rows_mock,
    )

    response = client.post(
        "/api/v1/vehicle_data/import",
        params={"vehicle_id": "car-1"},
        files={
            "file": (
                "vehicle-data.csv",
                b"invalid csv content",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Missing required columns: elevation"
    }

    import_rows_mock.assert_not_called()


def test_import_vehicle_csv_converts_unicode_error_to_422(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    decode_error = UnicodeDecodeError(
        "utf-8",
        b"\xff",
        0,
        1,
        "invalid start byte",
    )

    parse_csv_mock = MagicMock(side_effect=decode_error)

    monkeypatch.setattr(
        vehicle_data_api,
        "parse_csv",
        parse_csv_mock,
    )

    response = client.post(
        "/api/v1/vehicle_data/import",
        params={"vehicle_id": "car-1"},
        files={
            "file": (
                "vehicle-data.csv",
                b"\xff",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert "invalid start byte" in response.json()["detail"]


def test_import_vehicle_csv_converts_database_value_error_to_422(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
):
    parsed_rows = [MagicMock()]

    monkeypatch.setattr(
        vehicle_data_api,
        "parse_csv",
        MagicMock(return_value=parsed_rows),
    )
    monkeypatch.setattr(
        vehicle_data_api,
        "import_rows",
        MagicMock(
            side_effect=ValueError("Invalid database value")
        ),
    )

    response = client.post(
        "/api/v1/vehicle_data/import",
        params={"vehicle_id": "car-1"},
        files={
            "file": (
                "vehicle-data.csv",
                b"valid-looking-content",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    assert response.json() == {
        "detail": "Invalid database value"
    }


def test_import_vehicle_csv_requires_vehicle_id(
    client: TestClient,
):
    response = client.post(
        "/api/v1/vehicle_data/import",
        files={
            "file": (
                "vehicle-data.csv",
                b"csv content",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422


def test_import_vehicle_csv_rejects_empty_vehicle_id(
    client: TestClient,
):
    response = client.post(
        "/api/v1/vehicle_data/import",
        params={"vehicle_id": ""},
        files={
            "file": (
                "vehicle-data.csv",
                b"csv content",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    
