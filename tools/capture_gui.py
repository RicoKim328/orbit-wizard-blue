"""Capture real GUI views from an offline SGP4/IERS validation example.

Run on a desktop/Xvfb display from the repository root:
  .venv/bin/python tools/capture_gui.py --output-dir assets/screenshots
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from PySide6.QtCore import QDateTime, QTimeZone, QTimer
from PySide6.QtWidgets import QApplication, QHeaderView

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orbit_wizard_blue.gui import MainWindow  # noqa: E402
from orbit_wizard_blue.models import EarthData, OrbitRequest  # noqa: E402
from orbit_wizard_blue.orbit import compute_ephemeris  # noqa: E402
from validate_orbit import build_fixture  # noqa: E402


def example_inputs():
    """Use local validation GP elements and bundled Earth reference files."""
    snapshot, _, earth = build_fixture("meo")
    snapshot = replace(snapshot, source_url="local-example://validation-meo", source_kind="local",
                       source_metadata={"example_fixture": True})
    epoch = datetime.fromisoformat(str(snapshot.payload["EPOCH"])).replace(tzinfo=timezone.utc)
    request = OrbitRequest(epoch, epoch + timedelta(hours=12), 60)
    provenance = {}
    for key in ("iers", "leap_seconds"):
        provenance[key] = {
            "kind": "bundled", "source_url": f"Astropy 동봉 {key}",
            "fetched_at": "", "checked_at": "", "stale": False,
        }
    earth = EarthData(earth.iers_path, earth.leap_seconds_path, provenance)
    return snapshot, request, earth


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("assets/screenshots"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # No network service is constructed. The same propagation function used by
    # the app computes the displayed trajectory from local example inputs.
    snapshot, request, earth = example_inputs()
    result = compute_ephemeris(snapshot, request, earth)
    if result.gcrs_position_km is None or result.itrs_position_km is None:
        raise RuntimeError(f"Offline example lacks required coordinate frames: {result.warnings}")

    app = QApplication([])

    class OfflineService:
        pass

    user_state = TemporaryDirectory(prefix="orbit-wizard-capture-")
    window = MainWindow(service=OfflineService(), user_data_dir=Path(user_state.name))
    window.query.setText("VALIDATION MEO")
    window._show_matches([snapshot])
    window.start_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(request.start_utc.timestamp()), QTimeZone.utc()))
    window.end_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(request.end_utc.timestamp()), QTimeZone.utc()))
    window.step_edit.setValue(request.step_seconds)
    window._calculation_done((result, earth))
    selected_index = 180
    window.set_sample_index(selected_index)
    window.show()

    for table in window.tables:
        header = table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QHeaderView.Interactive)
        table.resizeColumnsToContents()
        table.setColumnWidth(0, max(230, table.columnWidth(0)))
        for column in range(1, table.model().columnCount()):
            table.setColumnWidth(column, max(115, table.columnWidth(column)))

    def save(filename: str, widget) -> bool:
        if widget.grab().save(str(args.output_dir / filename)):
            return True
        print(f"Could not save {filename}", file=sys.stderr)
        app.exit(4)
        return False

    def capture_gcrs() -> None:
        if not window.orbit_view.available or not window.orbit_view.view.isValid():
            print("OpenGL context is unavailable", file=sys.stderr)
            app.exit(1)
            return
        if window.slider.value() != selected_index or window.orbit_view.index != selected_index:
            app.exit(2)
            return
        if save("gcrs-window.png", window):
            window.frame_combo.setCurrentIndex(1)
            QTimer.singleShot(1000, capture_itrs)

    def capture_itrs() -> None:
        if window.slider.value() != selected_index or window.orbit_view.index != selected_index:
            app.exit(3)
            return
        if save("itrs-window.png", window):
            window.tabs.setCurrentWidget(window.ground_track_view)
            QTimer.singleShot(500, capture_ground_track)

    def capture_ground_track() -> None:
        if window.ground_track_view.index != selected_index:
            app.exit(5)
            return
        if save("ground-track.png", window):
            window.tabs.setCurrentWidget(window.tables[0])
            QTimer.singleShot(500, capture_teme_table)

    def capture_teme_table() -> None:
        if save("teme-table.png", window):
            window.tabs.setCurrentWidget(window.tables[1])
            QTimer.singleShot(500, capture_itrs_table)

    def capture_itrs_table() -> None:
        if save("itrs-table.png", window):
            window.show_data_status()
            window.data_status_dialog.resize(800, 820)
            QTimer.singleShot(500, capture_status)

    def capture_status() -> None:
        if save("data-status.png", window.data_status_dialog):
            print(f"Saved gcrs-window.png, itrs-window.png, ground-track.png, teme-table.png, itrs-table.png, "
                  f"data-status.png to {args.output_dir}")
            app.quit()

    QTimer.singleShot(2000, capture_gcrs)
    code = app.exec()
    user_state.cleanup()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
