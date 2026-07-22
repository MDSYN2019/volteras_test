import textwrap
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.models.vehicle_data import VehicleData
from app.services.csv_import import (
    _is_null,
    _nullable_float,
    _nullable_string,
    _required_float,
    import_rows,
    parse_csv,
    vehicle_id_from_path,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, True),
        ("", True),
        ("   ", True),
        ("NULL", True),
        ("null", True),
        ("None", True),
        ("N/A", True),
        ("  n/a  ", True),
        ("0", False),
        ("text", False),
    ],
)
def test_is_null(value, expected):
    assert _is_null(value) is expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("NULL", None),
        ("N/A", None),
        ("12.5", 12.5),
        (" 42 ", 42.0),
        ("0", 0.0),
    ],
)
def test_nullable_float(value, expected):
    assert _nullable_float(value) == expected


def test_nullable_float_rejects_invalid_number():
    with pytest.raises(ValueError):
        _nullable_float("not-a-number")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("NULL", None),
        ("N/A", None),
        (" D ", "D"),
        ("park", "park"),
    ],
)
def test_nullable_string(value, expected):
    assert _nullable_string(value) == expected


@pytest.mark.parametrize("value", [None, "", "   "])
def test_required_float_rejects_empty_value(value):
    with pytest.raises(
        ValueError,
        match="odometer cannot be empty",
    ):
        _required_float(value, "odometer")


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("12.5", 12.5),
        (" 42 ", 42.0),
        ("0", 0.0),
    ],
)
def test_required_float_returns_float(value, expected):
    assert _required_float(value, "odometer") == expected


def test_parse_csv_returns_vehicle_data_objects():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        2026-07-21T10:30:00Z,45.5,12000.25,82.0,35.2,D
        2026-07-21T10:31:00+00:00,,12001.0,81.5,36.0,NULL
        """
    ).encode("utf-8")

    rows = parse_csv(
        content=content,
        vehicle_id="car-1",
    )

    assert len(rows) == 2

    assert rows[0].vehicle_id == "car-1"
    assert rows[0].timestamp.isoformat() == "2026-07-21T10:30:00+00:00"
    assert rows[0].speed == 45.5
    assert rows[0].odometer == 12000.25
    assert rows[0].soc == 82.0
    assert rows[0].elevation == 35.2
    assert rows[0].shift_state == "D"

    assert rows[1].vehicle_id == "car-1"
    assert rows[1].speed is None
    assert rows[1].shift_state is None


def test_parse_csv_handles_utf8_bom():
    content = (
        "\ufefftimestamp,speed,odometer,soc,elevation,shift_state\n"
        "2026-07-21T10:30:00Z,45.5,12000,82,35,D\n"
    ).encode("utf-8")

    rows = parse_csv(content, vehicle_id="car-1")

    assert len(rows) == 1
    assert rows[0].vehicle_id == "car-1"


def test_parse_csv_allows_columns_in_different_order():
    content = textwrap.dedent(
        """\
        soc,vehicle_name,elevation,timestamp,shift_state,odometer,speed
        82,test vehicle,35,2026-07-21T10:30:00Z,D,12000,45
        """
    ).encode("utf-8")

    rows = parse_csv(content, vehicle_id="car-1")

    assert len(rows) == 1
    assert rows[0].speed == 45.0
    assert rows[0].soc == 82.0


def test_parse_csv_rejects_missing_columns():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,shift_state
        2026-07-21T10:30:00Z,45,12000,82,D
        """
    ).encode("utf-8")

    with pytest.raises(
        ValueError,
        match="Missing required columns: elevation",
    ):
        parse_csv(content, vehicle_id="car-1")


def test_parse_csv_reports_invalid_row_number():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        2026-07-21T10:30:00Z,45,12000,82,35,D
        2026-07-21T10:31:00Z,46,,81,36,D
        """
    ).encode("utf-8")

    with pytest.raises(
        ValueError,
        match="Invalid row 3: odometer cannot be empty",
    ):
        parse_csv(content, vehicle_id="car-1")


def test_parse_csv_rejects_invalid_timestamp():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        not-a-timestamp,45,12000,82,35,D
        """
    ).encode("utf-8")

    with pytest.raises(
        ValueError,
        match="Invalid row 2",
    ):
        parse_csv(content, vehicle_id="car-1")


def test_parse_csv_rejects_invalid_numeric_value():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        2026-07-21T10:30:00Z,fast,12000,82,35,D
        """
    ).encode("utf-8")

    with pytest.raises(
        ValueError,
        match="Invalid row 2",
    ):
        parse_csv(content, vehicle_id="car-1")


def test_import_rows_inserts_new_row():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        2026-07-21T10:30:00Z,45,12000,82,35,D
        """
    ).encode("utf-8")

    rows = parse_csv(content, vehicle_id="car-1")

    db = MagicMock(spec=Session)
    db.scalar.return_value = None

    inserted, skipped = import_rows(db, rows)

    assert inserted == 1
    assert skipped == 0

    db.scalar.assert_called_once()
    db.add.assert_called_once()
    db.commit.assert_called_once()

    added_vehicle = db.add.call_args.args[0]

    assert isinstance(added_vehicle, VehicleData)
    assert added_vehicle.vehicle_id == "car-1"
    assert added_vehicle.speed == 45.0
    assert added_vehicle.odometer == 12000.0


def test_import_rows_skips_existing_row():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        2026-07-21T10:30:00Z,45,12000,82,35,D
        """
    ).encode("utf-8")

    rows = parse_csv(content, vehicle_id="car-1")

    db = MagicMock(spec=Session)
    db.scalar.return_value = 123

    inserted, skipped = import_rows(db, rows)

    assert inserted == 0
    assert skipped == 1

    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_import_rows_counts_inserted_and_skipped_rows():
    content = textwrap.dedent(
        """\
        timestamp,speed,odometer,soc,elevation,shift_state
        2026-07-21T10:30:00Z,45,12000,82,35,D
        2026-07-21T10:31:00Z,46,12001,81,36,D
        """
    ).encode("utf-8")

    rows = parse_csv(content, vehicle_id="car-1")

    db = MagicMock(spec=Session)

    # First row does not exist; second row already exists.
    db.scalar.side_effect = [None, 456]

    inserted, skipped = import_rows(db, rows)

    assert inserted == 1
    assert skipped == 1

    assert db.scalar.call_count == 2
    assert db.add.call_count == 1
    db.commit.assert_called_once()


def test_import_rows_handles_empty_list():
    db = MagicMock(spec=Session)

    inserted, skipped = import_rows(db, [])

    assert inserted == 0
    assert skipped == 0

    db.scalar.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_called_once()


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        (Path("/data/car-1.csv"), "car-1"),
        (
            Path("/data/06ab31a9-b35d-4e47-8e44-9c35feb1bfae.csv"),
            "06ab31a9-b35d-4e47-8e44-9c35feb1bfae",
        ),
        (Path("/data/vehicle.data.csv"), "vehicle.data"),
    ],
)
def test_vehicle_id_from_path(path, expected):
    assert vehicle_id_from_path(path) == expected


def test_vehicle_id_from_path_rejects_empty_vehicle_id():
    path = Path("   .csv")

    with pytest.raises(
        ValueError,
        match="CSV filename must contain a vehicle id",
    ):
        vehicle_id_from_path(path)
