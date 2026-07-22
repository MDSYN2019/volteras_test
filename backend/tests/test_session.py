from unittest.mock import MagicMock

import pytest
from sqlalchemy.orm import Session

from app.db import session as session_module


def test_get_db_yields_session_and_closes_it(
    monkeypatch: pytest.MonkeyPatch,
):
    mock_db = MagicMock(spec=Session)
    mock_session_local = MagicMock(return_value=mock_db)

    monkeypatch.setattr(
        session_module,
        "SessionLocal",
        mock_session_local,
    )

    generator = session_module.get_db()

    yielded_db = next(generator)

    assert yielded_db is mock_db
    mock_session_local.assert_called_once_with()
    mock_db.close.assert_not_called()

    with pytest.raises(StopIteration):
        next(generator)

    mock_db.close.assert_called_once_with()


def test_get_db_closes_session_when_exception_occurs(
    monkeypatch: pytest.MonkeyPatch,
):
    mock_db = MagicMock(spec=Session)

    monkeypatch.setattr(
        session_module,
        "SessionLocal",
        MagicMock(return_value=mock_db),
    )

    generator = session_module.get_db()

    yielded_db = next(generator)

    assert yielded_db is mock_db

    with pytest.raises(RuntimeError, match="endpoint failed"):
        generator.throw(RuntimeError("endpoint failed"))

    mock_db.close.assert_called_once_with()
