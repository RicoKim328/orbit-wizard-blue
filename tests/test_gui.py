"""GUI behavior that must stay consistent across views and time zones."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPlainTextEdit

os.environ["ORBIT_WIZARD_DISABLE_3D"] = "1"

from orbit_wizard_blue.gui.window import MainWindow  # noqa: E402
from orbit_wizard_blue.models import DataSnapshot, EarthData, OrbitRequest, OrbitResult  # noqa: E402


class StubService:
    pass


@pytest.fixture
def window(qtbot):
    widget = MainWindow(service=StubService())
    qtbot.addWidget(widget)
    return widget


def make_result(count=3, provenance=None):
    start = datetime(2026, 10, 15, tzinfo=timezone.utc)
    snapshot = DataSnapshot(
        {"OBJECT_NAME": "TEST", "NORAD_CAT_ID": 42, "EPOCH": start.isoformat()},
        "local", start.isoformat(), start.isoformat(), "hash",
    )
    times = tuple((start + timedelta(seconds=60 * i)).isoformat().replace("+00:00", "Z") for i in range(count))
    position = np.repeat([[7000.0, 0.0, 0.0]], count, axis=0)
    velocity = np.repeat([[0.0, 7.5, 0.0]], count, axis=0)
    return OrbitResult(snapshot, OrbitRequest(start, start + timedelta(seconds=60 * (count - 1))),
                       times, position, velocity, position, velocity, position, position,
                       np.repeat(np.eye(3)[None, :, :], count, axis=0),
                       provenance=provenance or {})


def test_default_inputs_are_utc_and_24_hours(window):
    assert window.start_edit.timeZone().id() == b"UTC"
    assert window.end_edit.timeZone().id() == b"UTC"
    assert window._date_utc(window.end_edit) - window._date_utc(window.start_edit) == timedelta(hours=24)
    assert window.step_edit.value() == 60


def test_sample_selection_stays_synchronized(window):
    window._calculation_done(make_result())
    window.slider.setValue(2)
    assert all(table.selectionModel().currentIndex().row() == 2 for table in window.tables)
    assert window.orbit_view.index == 2
    window.tables[0].selectRow(1)
    assert window.slider.value() == 1
    assert window.orbit_view.index == 1


def test_playback_uses_sample_times_without_interpolation(window, monkeypatch):
    import orbit_wizard_blue.gui.window as gui_window

    window._calculation_done(make_result())
    clock = [100.0]
    monkeypatch.setattr(gui_window, "monotonic", lambda: clock[0])
    window._toggle_play()
    clock[0] = 100.5  # 30 simulated seconds at the default 60x speed.
    window._play_tick()
    assert window.slider.value() == 0
    clock[0] = 101.0
    window._play_tick()
    assert window.slider.value() == 1
    clock[0] = 102.0
    window._play_tick()
    assert window.slider.value() == 2
    assert not window._playing


def test_table_model_reads_immutable_result(window):
    result = make_result()
    window._calculation_done(result)
    model = window.models[0]
    assert model.rowCount() == 3
    assert model.data(model.index(0, 1), Qt.DisplayRole) == "7,000.000000"
    assert not result.teme_position_km.flags.writeable


def test_data_status_distinguishes_current_and_result_sources(window, tmp_path):
    result = make_result(provenance={"earth_data": {
        "iers": {"kind": "bundled", "sha256": "old", "source_url": "bundled-iers", "stale": True},
        "leap_seconds": {"kind": "bundled", "sha256": "leaps", "source_url": "bundled-leaps"},
    }})
    window._show_matches([result.satellite])
    window._calculation_done(result)
    earth = EarthData(tmp_path / "iers", tmp_path / "leaps", {
        "iers": {"kind": "downloaded", "sha256": "new", "fetched_at": "2026-10-15T00:00:00Z",
                 "checked_at": "2026-10-15T00:01:00Z", "source_url": "online-iers", "stale": False},
        "leap_seconds": {"kind": "bundled", "sha256": "leaps", "source_url": "bundled-leaps"},
    })
    cached_snapshot = DataSnapshot(result.satellite.payload, result.satellite.source_url,
                                   result.satellite.fetched_at, result.satellite.checked_at,
                                   result.satellite.sha256, stale=True, warning="offline cache")
    window._refresh_done((cached_snapshot, earth))
    assert "다시 계산" in window.recompute_notice.text()
    window.show_data_status()
    details = window.data_status_dialog.findChild(QPlainTextEdit)
    text = details.toPlainText()
    assert "현재 선택 GP 자료" in text
    assert "표시된 계산 결과의 GP 자료" in text
    assert "캐시 상태: 오래됨" in text
    assert "offline cache" in text
    assert "다운로드 자료 · 캐시 유효" in text
    assert "2026-10-15T00:01:00Z" in text
    assert "online-iers" in text and "bundled-iers" in text
