"""Application and frozen-bundle entry point."""

from __future__ import annotations

import argparse
import json
import sys
import traceback


def smoke_test() -> int:
    """Check frozen imports, local GP conversion, transforms, and export offline."""
    from datetime import datetime, timedelta, timezone
    from pathlib import Path
    from tempfile import TemporaryDirectory

    import astropy
    import OpenGL
    import pyqtgraph
    import pyqtgraph.opengl as gl
    from PySide6 import QtCore
    from PySide6.QtWidgets import QApplication
    from astropy.utils import iers

    from orbit_wizard_blue.export import export_ephemeris
    from orbit_wizard_blue.models import DataSnapshot, EarthData, OrbitRequest
    from orbit_wizard_blue.orbit import _satrec, compute_ephemeris

    app = QApplication.instance() or QApplication([])
    if app is None:
        raise RuntimeError("Qt application initialization failed")
    if not hasattr(gl, "GLViewWidget"):
        raise RuntimeError("PyQtGraph OpenGL integration unavailable")
    epoch = datetime(2024, 1, 1, tzinfo=timezone.utc)
    payload = {
        "OBJECT_NAME": "SMOKE SAT", "NORAD_CAT_ID": 25544,
        "EPOCH": epoch.isoformat(), "MEAN_MOTION": 15.5, "ECCENTRICITY": 0.0005,
        "INCLINATION": 51.6, "RA_OF_ASC_NODE": 75.0,
        "ARG_OF_PERICENTER": 120.0, "MEAN_ANOMALY": 240.0,
    }
    snapshot = DataSnapshot(payload, "local-smoke", epoch.isoformat(), epoch.isoformat(), "local")
    satellite = _satrec(snapshot)
    if satellite.satnum != 25544:
        raise RuntimeError("GP JSON conversion failed")
    earth = EarthData(Path(iers.IERS_A_FILE), Path(iers.IERS_LEAP_SECOND_FILE), {"kind": "bundled"})
    result = compute_ephemeris(snapshot, OrbitRequest(epoch, epoch + timedelta(minutes=2), 60), earth)
    if len(result.times_utc) != 3 or result.itrs_position_km is None or result.gcrs_position_km is None:
        raise RuntimeError(f"Orbit transform failed: {result.warnings}")
    with TemporaryDirectory() as temp_dir:
        csv_path, metadata_path = export_ephemeris(result, Path(temp_dir) / "smoke.csv")
        if not csv_path.read_bytes().startswith(b"\xef\xbb\xbf") or not metadata_path.exists():
            raise RuntimeError("CSV or metadata export failed")
    print(f"Smoke OK: Qt {QtCore.__version__}, PyQtGraph {pyqtgraph.__version__}, "
          f"PyOpenGL {OpenGL.__version__}, Astropy {astropy.__version__}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="위성 궤도 분석 데스크톱 앱")
    parser.add_argument("--smoke-test", action="store_true", help="GUI를 열지 않고 배포본 기본 검증")
    parser.add_argument("--smoke-output", type=str, help="기본 검증 결과 JSON 파일")
    args = parser.parse_args()
    if args.smoke_test:
        try:
            result = smoke_test()
            report = {"status": "ok"}
        except Exception:
            result = 1
            report = {"status": "failed", "traceback": traceback.format_exc()}
            print(report["traceback"], file=sys.stderr)
        if args.smoke_output:
            from pathlib import Path

            Path(args.smoke_output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return result
    from PySide6.QtWidgets import QApplication

    from orbit_wizard_blue.gui import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("orbit-wizard-blue")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
