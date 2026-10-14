"""Capture real OpenGL GCRS/ITRS GUI screenshots without any network access."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PySide6.QtCore import QDateTime, QTimeZone, QTimer
from PySide6.QtWidgets import QApplication

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orbit_wizard_blue.gui import MainWindow  # noqa: E402
from orbit_wizard_blue.models import DataSnapshot, OrbitRequest, OrbitResult  # noqa: E402


def fixture_result() -> OrbitResult:
    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    count = 121
    seconds = np.arange(count) * 60.0
    angle = seconds * (2 * np.pi / (92 * 60))
    itrs = np.column_stack((7000 * np.cos(angle), 7000 * np.sin(angle) * 0.7,
                            7000 * np.sin(angle) * 0.7))
    velocity = np.gradient(itrs, 60.0, axis=0)
    spin = seconds * (2 * np.pi / 86164.0)
    rotation = np.zeros((count, 3, 3))
    rotation[:, 0, 0] = np.cos(spin)
    rotation[:, 0, 1] = -np.sin(spin)
    rotation[:, 1, 0] = np.sin(spin)
    rotation[:, 1, 1] = np.cos(spin)
    rotation[:, 2, 2] = 1
    gcrs = np.einsum("nij,nj->ni", rotation, itrs)
    snapshot = DataSnapshot({"OBJECT_NAME": "OFFLINE DEMO", "NORAD_CAT_ID": 99999,
                             "EPOCH": start.isoformat()}, "offline-fixture", start.isoformat(),
                            start.isoformat(), "fixture")
    times = tuple((start + timedelta(seconds=int(t))).isoformat().replace("+00:00", "Z") for t in seconds)
    geodetic = np.zeros((count, 3))
    return OrbitResult(snapshot, OrbitRequest(start, start + timedelta(seconds=int(seconds[-1]))),
                       times, itrs, velocity, itrs, velocity, gcrs, geodetic, rotation)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("/tmp/orbit-wizard-screenshots"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    app = QApplication([])

    class OfflineService:
        pass

    window = MainWindow(service=OfflineService())
    result = fixture_result()
    window.query.setText("OFFLINE DEMO")
    window._show_matches([result.satellite])
    window.start_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(result.request.start_utc.timestamp()),
                                                             QTimeZone.utc()))
    window.end_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(result.request.end_utc.timestamp()),
                                                           QTimeZone.utc()))
    window.step_edit.setValue(result.request.step_seconds)
    window._calculation_done(result)
    window.set_sample_index(40)
    window.show()

    def capture_gcrs():
        if not window.orbit_view.available or not window.orbit_view.view.isValid():
            print("OpenGL context is unavailable", file=sys.stderr)
            app.exit(1)
            return
        if window.slider.value() != 40 or window.orbit_view.index != 40:
            app.exit(2)
            return
        window.grab().save(str(args.output_dir / "gcrs-window.png"))
        window.orbit_view.view.grabFramebuffer().save(str(args.output_dir / "gcrs-3d.png"))
        window.frame_combo.setCurrentIndex(1)
        QTimer.singleShot(2000, capture_itrs)

    def capture_itrs():
        if window.slider.value() != 40 or window.orbit_view.index != 40:
            app.exit(3)
            return
        window.grab().save(str(args.output_dir / "itrs-window.png"))
        window.orbit_view.view.grabFramebuffer().save(str(args.output_dir / "itrs-3d.png"))
        print(f"Saved screenshots to {args.output_dir}")
        app.quit()

    QTimer.singleShot(2000, capture_gcrs)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
