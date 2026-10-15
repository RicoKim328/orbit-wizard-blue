"""Bounded, offline visual validation of the frozen desktop application."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
import inspect
import os
from pathlib import Path
import platform
import socket
import sys
from tempfile import TemporaryDirectory
import traceback
from typing import Any


class _OfflineService:
    """Fail closed if the validation GUI unexpectedly requests provider data."""

    def __init__(self, earth=None):
        self.earth = earth

    def get_earth_data(self, *, cancel=None, status=None, force=False):
        if cancel is not None and cancel():
            raise RuntimeError("GUI validation was cancelled")
        return self.earth

    def __getattr__(self, name: str) -> Any:
        raise RuntimeError(f"Unexpected data service call during offline GUI validation: {name}")


def _fixture():
    from astropy.utils import iers

    from .models import DataSnapshot, EarthData, OrbitRequest
    from .orbit import compute_ephemeris

    epoch = datetime(2024, 1, 1, tzinfo=timezone.utc)
    payload = {
        "OBJECT_NAME": "OFFLINE VALIDATION SATELLITE",
        "OBJECT_ID": "2024-001A",
        "NORAD_CAT_ID": 100001,
        "EPOCH": "2024-01-01T00:00:00.000000",
        "MEAN_MOTION": 15.5,
        "ECCENTRICITY": 0.0005,
        "INCLINATION": 51.6,
        "RA_OF_ASC_NODE": 75.0,
        "ARG_OF_PERICENTER": 120.0,
        "MEAN_ANOMALY": 240.0,
        "BSTAR": 0.0,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    stamp = "2024-01-01T00:00:00Z"
    source = DataSnapshot(payload, "fixture://offline-gui", stamp, stamp, sha256(encoded).hexdigest(),
                          source_kind="local", source_format="gp_json",
                          source_metadata={"validation_fixture": True})
    request = OrbitRequest(epoch, epoch + timedelta(hours=3), 60)
    earth = EarthData(Path(iers.IERS_A_FILE), Path(iers.IERS_LEAP_SECOND_FILE),
                      {"kind": "bundled", "validation_fixture": True})
    result = compute_ephemeris(source, request, earth)
    if result.itrs_position_km is None or result.gcrs_position_km is None or result.geodetic_deg_km is None:
        raise RuntimeError(f"Offline fixture coordinate transforms failed: {result.warnings}")
    return source, earth, result


def _opengl_diagnostics(orbit_view) -> dict[str, Any]:
    """Describe the GL library and renderer bound to the displayed widget."""
    from OpenGL import platform as gl_platform

    details: dict[str, Any] = {
        "pyopengl_platform_class": type(gl_platform.PLATFORM).__name__,
        "pyopengl_gl_library": str(getattr(gl_platform.PLATFORM.GL, "_name", "")),
    }
    if not orbit_view.available or not orbit_view.view.isValid():
        from PySide6.QtWidgets import QLabel

        labels = [label.text() for label in orbit_view.findChildren(QLabel) if label.text()]
        details["fallback_reason"] = labels[-1] if labels else "OpenGL widget is unavailable or invalid"
        return details

    from OpenGL import GL
    from PySide6.QtGui import QOpenGLContext

    view = orbit_view.view
    try:
        view.makeCurrent()
        if QOpenGLContext.currentContext() is None:
            details["fallback_reason"] = "makeCurrent did not activate an OpenGL context"
            return details
        for key, token in (("gl_vendor", GL.GL_VENDOR), ("gl_renderer", GL.GL_RENDERER),
                           ("gl_version", GL.GL_VERSION)):
            value = GL.glGetString(token)
            details[key] = value.decode("utf-8", errors="replace") if isinstance(value, bytes) else str(value or "")
        if not all(details[key] for key in ("gl_vendor", "gl_renderer", "gl_version")):
            details["fallback_reason"] = "OpenGL context returned empty vendor, renderer, or version"
    except Exception as exc:
        details["fallback_reason"] = f"OpenGL diagnostics failed: {type(exc).__name__}: {exc}"
    finally:
        view.doneCurrent()
    return details


def run_gui_check(output_dir: Path) -> int:
    """Show and inspect the real GUI, save three images and a JSON report.

    A missing display or OpenGL context is a failed check, never an implicit
    skip. The report records the host OS; it does not claim physical Windows 11
    or GPU validation when run on CI or Xvfb.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "status": "failed",
        "environment": {
            "platform": platform.platform(),
            "system": platform.system(),
            "python": platform.python_version(),
            "qt_platform_requested": os.environ.get("QT_QPA_PLATFORM", ""),
            "qt_opengl_requested": os.environ.get("QT_OPENGL", ""),
            "pyopengl_platform_requested": os.environ.get("PYOPENGL_PLATFORM", ""),
            "ci": bool(os.environ.get("CI")),
            "physical_windows_11_gpu_verified": False,
        },
        "fixture": {"source_kind": "local", "network_allowed": False},
        "checks": {},
        "screenshots": {},
    }
    report_path = output_dir / "gui-check-report.json"
    if sys.platform.startswith("linux") and not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")
                                                 or os.environ.get("QT_QPA_PLATFORM")):
        report["error"] = "No Qt display is configured"
        report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        return 1

    isolated_vars = ("XDG_CACHE_HOME", "XDG_CONFIG_HOME", "XDG_DATA_HOME", "APPDATA", "LOCALAPPDATA",
                     "ORBIT_WIZARD_LOG_DIR")
    previous_env = {name: os.environ.get(name) for name in isolated_vars}
    original_connect = socket.socket.connect
    original_create_connection = socket.create_connection

    def blocked_connection(*args, **kwargs):
        raise RuntimeError("Network access attempted during offline GUI validation")

    with TemporaryDirectory(prefix="orbit-wizard-gui-check-") as scratch:
        for name in isolated_vars:
            os.environ[name] = scratch
        socket.socket.connect = blocked_connection
        socket.create_connection = blocked_connection
        try:
            from .gl_platform import configure_pyopengl

            configure_pyopengl()
            report["environment"]["qt_opengl_requested"] = os.environ.get("QT_OPENGL", "")
            report["environment"]["pyopengl_platform_requested"] = os.environ.get("PYOPENGL_PLATFORM", "")
            from PySide6.QtCore import QDateTime, QTimeZone, QTimer
            from PySide6.QtWidgets import QApplication

            from .gui.window import MainWindow

            source, earth, result = _fixture()
            app = QApplication.instance() or QApplication([])
            report["environment"]["qt_platform_actual"] = app.platformName()
            window_kwargs: dict[str, Any] = {"service": _OfflineService(earth)}
            if "user_data_dir" in inspect.signature(MainWindow).parameters:
                window_kwargs["user_data_dir"] = Path(scratch)
            window = MainWindow(**window_kwargs)
            window._show_matches([source])
            for edit, instant in ((window.start_edit, result.request.start_utc),
                                  (window.end_edit, result.request.end_utc)):
                edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(instant.timestamp()), QTimeZone.utc()))
            window.step_edit.setValue(result.request.step_seconds)
            window._calculation_done((result, earth))
            selected_index = 42
            window.set_sample_index(selected_index)
            window.show()
            finished = False

            def capture(label: str) -> None:
                app.processEvents()
                path = output_dir / f"gui-{label}.png"
                pixmap = window.grab()
                if pixmap.isNull() or not pixmap.save(str(path), "PNG") or path.stat().st_size < 1000:
                    raise RuntimeError(f"Could not save {label} GUI screenshot")
                report["screenshots"][label] = path.name

            def finish(error: str | None = None) -> None:
                nonlocal finished
                if finished:
                    return
                finished = True
                if error:
                    report["error"] = error
                else:
                    report["status"] = "ok"
                window.close()
                app.quit()

            def guarded(callback):
                def call():
                    try:
                        callback()
                    except Exception:
                        finish(traceback.format_exc())
                return call

            def stage_gcrs() -> None:
                checks = report["checks"]
                checks["window_visible"] = window.isVisible()
                checks["sample_count"] = len(result.times_utc)
                checks["local_source_shown"] = (
                    window.snapshot is not None and window.snapshot.source_kind == "local"
                    and "OFFLINE VALIDATION SATELLITE" in window.result_summary.text()
                )
                checks["selected_sample"] = window.slider.value() == selected_index
                checks["tables_synchronized"] = all(
                    table.selectionModel().currentIndex().row() == selected_index
                    and table.model().rowCount() == len(result.times_utc) for table in window.tables
                )
                checks["gcrs_selected"] = window.frame_combo.currentData() == "GCRS" and window.orbit_view.frame == "GCRS"
                checks["opengl_context"] = bool(window.orbit_view.available and window.orbit_view.view.isValid())
                report["opengl"] = _opengl_diagnostics(window.orbit_view)
                checks["opengl_renderer_identified"] = all(
                    report["opengl"].get(key) for key in ("gl_vendor", "gl_renderer", "gl_version")
                )
                capture("gcrs")
                window.frame_combo.setCurrentIndex(1)
                QTimer.singleShot(250, guarded(stage_itrs))

            def stage_itrs() -> None:
                checks = report["checks"]
                checks["itrs_selected"] = window.frame_combo.currentData() == "ITRS" and window.orbit_view.frame == "ITRS"
                checks["orbit_marker_synchronized"] = window.orbit_view.index == selected_index
                capture("itrs")
                window.tabs.setCurrentIndex(1)
                QTimer.singleShot(250, guarded(stage_map))

            def stage_map() -> None:
                checks = report["checks"]
                checks["map_selected"] = window.tabs.currentIndex() == 1
                checks["map_track_available"] = window.ground_track_view._track_available
                checks["map_marker_synchronized"] = window.ground_track_view.index == selected_index
                checks["map_sample_time_shown"] = result.times_utc[selected_index] in window.ground_track_view.sample_label.text()
                window.ground_track_view.fit_world()
                app.processEvents()
                x_range, y_range = window.ground_track_view.plot.getViewBox().viewRange()
                report["map_view_range_deg"] = {"longitude": x_range, "latitude": y_range}
                checks["map_full_world_extent"] = (
                    x_range[0] <= -179.5 and x_range[1] >= 179.5
                    and y_range[0] <= -89.5 and y_range[1] >= 89.5
                )
                capture("ground-track")
                QTimer.singleShot(100, guarded(stage_manual))

            def stage_manual() -> None:
                manual = window.manual_input
                window.source_tabs.setCurrentWidget(manual)
                manual.name_edit.setText("FROZEN MANUAL VALIDATION")
                manual.epoch_edit.setDateTime(QDateTime.fromSecsSinceEpoch(
                    int(result.request.start_utc.timestamp()), QTimeZone.utc()))
                manual.element_edits["raan_deg"].setValue(75)
                manual.element_edits["argp_deg"].setValue(120)
                manual.element_edits["true_anomaly_deg"].setValue(240)
                window.end_edit.setDateTime(QDateTime.fromSecsSinceEpoch(
                    int((result.request.start_utc + timedelta(minutes=2)).timestamp()), QTimeZone.utc()))
                window.calculate()
                QTimer.singleShot(50, guarded(wait_for_manual))

            def wait_for_manual() -> None:
                if window._thread is not None:
                    QTimer.singleShot(50, guarded(wait_for_manual))
                    return
                manual_result = window.result
                checks = report["checks"]
                checks["manual_source_shown"] = (
                    manual_result is not None and manual_result.satellite.source_kind == "manual"
                    and window.source_tabs.currentWidget() is window.manual_input
                )
                if checks["manual_source_shown"]:
                    checks["manual_native_gcrs"] = manual_result.native_frame == "GCRS"
                    checks["manual_sample_count"] = len(manual_result.times_utc) == 3
                    checks["manual_gcrs_state"] = (
                        manual_result.gcrs_position_km is not None
                        and manual_result.gcrs_velocity_km_s is not None
                        and window.models[2].data(window.models[2].index(0, 1)) not in (None, "—")
                    )
                    checks["manual_views_synchronized"] = (
                        window.orbit_view.index == window.slider.value()
                        and window.ground_track_view.index == window.slider.value()
                        and all(table.selectionModel().currentIndex().row() == window.slider.value()
                                for table in window.tables)
                    )
                    checks["manual_3d_context"] = bool(window.orbit_view.available and window.orbit_view.view.isValid())
                    checks["manual_ground_track"] = window.ground_track_view._track_available
                window.tabs.setCurrentWidget(window.tables[2])
                QTimer.singleShot(250, guarded(stage_manual_capture))

            def stage_manual_capture() -> None:
                capture("manual")
                checks = report["checks"]
                failures = [name for name, value in checks.items() if isinstance(value, bool) and not value]
                finish("GUI checks failed: " + ", ".join(failures) if failures else None)

            QTimer.singleShot(300, guarded(stage_gcrs))
            QTimer.singleShot(30_000, guarded(lambda: finish("GUI validation timed out after 30 seconds")))
            app.exec()
            if not finished:
                report["error"] = "Qt event loop exited before GUI validation completed"
        except Exception:
            report["error"] = traceback.format_exc()
        finally:
            socket.socket.connect = original_connect
            socket.create_connection = original_create_connection
            for name, previous in previous_env.items():
                if previous is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = previous
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if report["status"] == "ok" else 1
