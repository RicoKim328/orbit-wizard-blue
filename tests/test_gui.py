"""GUI behavior that must stay consistent across views and time zones."""

from __future__ import annotations

import os
import json
from threading import get_ident
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import numpy as np
import pytest
from PySide6.QtCore import QDateTime, QTimeZone, Qt
from PySide6.QtWidgets import QPlainTextEdit

os.environ["ORBIT_WIZARD_DISABLE_3D"] = "1"

from orbit_wizard_blue.gui.window import MainWindow  # noqa: E402
from orbit_wizard_blue.gui.tables import configure_table_columns  # noqa: E402
from orbit_wizard_blue.gui.ground_track_view import coastline_points  # noqa: E402
from orbit_wizard_blue.models import DataSnapshot, EarthData, OrbitRequest, OrbitResult  # noqa: E402


class StubService:
    pass


@pytest.fixture
def window(qtbot, tmp_path):
    widget = MainWindow(service=StubService(), user_data_dir=tmp_path)
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
    geodetic = np.column_stack((np.full(count, 10.0),
                                np.linspace(179.0, 181.0, count), np.full(count, 500.0)))
    return OrbitResult(snapshot, OrbitRequest(start, start + timedelta(seconds=60 * (count - 1))),
                       times, position, velocity, position, velocity, position, geodetic,
                       np.repeat(np.eye(3)[None, :, :], count, axis=0),
                       provenance=provenance or {})


def set_inputs_to_result(window, result):
    request = result.request
    window.start_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(request.start_utc.timestamp()), QTimeZone.utc()))
    window.end_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(request.end_utc.timestamp()), QTimeZone.utc()))
    window.step_edit.setValue(request.step_seconds)


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
    set_inputs_to_result(window, result)
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
    assert "IERS/윤초 자료" in window.recompute_notice.text()
    window.show_data_status()
    details = window.data_status_dialog.findChild(QPlainTextEdit)
    text = details.toPlainText()
    assert "현재 선택 위성 자료" in text
    assert "표시된 계산 결과의 위성 자료" in text
    assert "캐시 상태: 오래됨" in text
    assert "offline cache" in text
    assert "다운로드 자료 · 캐시 유효" in text
    assert "2026-10-15T00:01:00Z" in text
    assert "online-iers" in text and "bundled-iers" in text


def test_result_summary_and_request_mismatch_clear_after_revert(window):
    result = make_result()
    set_inputs_to_result(window, result)
    window._show_matches([result.satellite])
    window._calculation_done(result)
    assert window.recompute_notice.text() == ""
    summary = window.result_summary.text()
    assert "TEST · NORAD 42" in summary
    assert "출처: local" in summary
    assert "2026-10-15 00:00:00 UTC" in summary
    assert "60초 간격" in summary
    window.step_edit.setValue(120)
    assert "UTC 계산 구간/간격" in window.recompute_notice.text()
    assert window.export_button.isEnabled()
    assert window.result_summary.text() == summary
    window.step_edit.setValue(60)
    assert window.recompute_notice.text() == ""


def test_selection_change_and_revert_preserve_old_result(window):
    result = make_result()
    set_inputs_to_result(window, result)
    window._show_matches([result.satellite])
    window._calculation_done(result)
    other = DataSnapshot({"OBJECT_NAME": "OTHER", "NORAD_CAT_ID": 99}, "other",
                         "2026-10-15T00:00:00Z", "2026-10-15T00:00:00Z", "other-hash")
    window._show_matches([other])
    assert "선택 위성" in window.recompute_notice.text()
    assert window.result is result
    assert "TEST · NORAD 42" in window.result_summary.text()
    window._show_matches([result.satellite])
    assert window.recompute_notice.text() == ""


def test_calculation_completion_uses_captured_request_after_input_edit(window):
    result = make_result()
    set_inputs_to_result(window, result)
    window._show_matches([result.satellite])
    window.step_edit.setValue(90)  # A user edit while calculation is in progress.
    window._calculation_done(result)
    assert "60초 간격" in window.result_summary.text()
    assert "UTC 계산 구간/간격" in window.recompute_notice.text()
    window.step_edit.setValue(60)
    assert window.recompute_notice.text() == ""


def test_table_columns_allow_full_utc_and_numeric_values_without_row_scan(window, monkeypatch):
    table = window.tables[0]
    model = window.models[0]
    monkeypatch.setattr(model, "data", lambda *_args: (_ for _ in ()).throw(AssertionError("row scan")))
    configure_table_columns(table, "TEME")
    metrics = table.fontMetrics()
    assert not table.horizontalHeader().stretchLastSection()
    assert table.columnWidth(0) >= metrics.horizontalAdvance("2026-12-31T23:59:59.999999Z") + 24
    assert table.columnWidth(1) >= metrics.horizontalAdvance("-123,456.123456") + 24


def test_ground_track_uses_bundled_coastline_and_shared_sample_index(window):
    coast_lon, coast_lat = coastline_points()
    assert len(coast_lon) == len(coast_lat) and np.isfinite(coast_lon).sum() > 1_000
    result = make_result()
    window._calculation_done(result)
    track_lon, track_lat = window.ground_track_view.track.getData()
    assert np.isnan(track_lon).any()  # The 180° crossing has a visible gap.
    assert len(track_lon) == len(track_lat)
    window.slider.setValue(2)
    assert window.ground_track_view.index == 2
    assert "경도 -179.000000°" in window.ground_track_view.sample_label.text()
    window.tables[0].selectRow(1)
    assert window.ground_track_view.index == 1


def test_ground_track_explains_missing_geodetic_data(window):
    result = replace(make_result(), geodetic_deg_km=None)
    window._calculation_done(result)
    assert "측지 변환 자료가 없어" in window.ground_track_view.sample_label.text()
    assert window.ground_track_view.marker.getData()[0].size == 0


def test_ground_track_fit_shows_both_dateline_edges(window):
    view = window.ground_track_view
    view.resize(400, 700)
    view.fit_world()
    horizontal, vertical = view.plot.getViewBox().viewRange()
    assert horizontal[0] <= -180 and horizontal[1] >= 180
    assert vertical[0] <= -90 and vertical[1] >= 90


def test_local_import_recent_and_favorite_reopen_without_original(window, tmp_path, qtbot):
    payload = {"OBJECT_NAME": "LOCAL", "NORAD_CAT_ID": 12345, "EPOCH": "2026-10-15T00:00:00",
               "MEAN_MOTION": 15.0, "ECCENTRICITY": 0.001, "INCLINATION": 51.6,
               "RA_OF_ASC_NODE": 32.0, "ARG_OF_PERICENTER": 12.0, "MEAN_ANOMALY": 8.0}
    original = tmp_path / "local.json"
    original.write_text(json.dumps([payload, {**payload, "NORAD_CAT_ID": 12346}]), encoding="utf-8")
    snapshots = window.local_service.import_file(original)
    window._import_done(original.name, snapshots)
    assert window.matches.count() == 2
    assert "2026-10-15T00:00:00" in window.matches.item(0).text()
    assert "로컬 파일" in window.source_status.text()
    assert window.store.list_recent()[0].record_index is None
    window.matches.setCurrentRow(1)
    window.toggle_favorite()
    assert len(window.store.list_favorites()) == 1
    original.unlink()

    reopened = MainWindow(service=StubService(), user_data_dir=tmp_path)
    qtbot.addWidget(reopened)
    assert reopened.matches.count() == 0
    assert reopened.recent_list.count() == 1
    assert reopened.favorite_list.count() == 1
    reopened._open_recent(reopened.recent_list.item(0))
    qtbot.waitUntil(lambda: reopened._thread is None, timeout=5000)
    assert reopened.matches.count() == 2
    assert reopened.store.list_recent()[0].record_index is None
    reopened._open_favorite(reopened.favorite_list.item(0))
    qtbot.waitUntil(lambda: reopened._thread is None, timeout=5000)
    assert reopened.snapshot.payload["NORAD_CAT_ID"] == 12346
    reopened.favorite_list.setCurrentRow(0)
    reopened.remove_selected_favorite()
    assert reopened.favorite_list.count() == 0
    reopened.recent_list.setCurrentRow(0)
    reopened.remove_recent()
    assert reopened.recent_list.count() == 0


def test_online_favorite_rechecks_source_when_opened(window, qtbot, monkeypatch):
    snapshot = make_result().satellite
    resolved = replace(snapshot, sha256="new-hash")

    class OnlineService:
        def __init__(self):
            self.calls = []

        def get_satellite(self, norad_id, *, cancel, status):
            self.calls.append(norad_id)
            status("캐시 확인 중")
            return resolved

    window.service = OnlineService()
    main_thread = get_ident()
    callback_threads = []
    original_done = window._favorite_done

    def record_done(value):
        callback_threads.append(get_ident())
        original_done(value)

    monkeypatch.setattr(window, "_favorite_done", record_done)
    window.store.add_favorite(snapshot)
    window._load_user_lists()
    assert window.service.calls == []  # Startup/listing remains offline.
    window._open_favorite(window.favorite_list.item(0))
    qtbot.waitUntil(lambda: window._thread is None, timeout=5000)
    assert window.service.calls == ["42"]
    assert callback_threads == [main_thread]
    assert window.snapshot.sha256 == "new-hash"
    assert window.source_tabs.currentWidget() is window.matches
