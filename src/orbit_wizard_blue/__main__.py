"""Application and frozen-bundle entry point."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from logging.handlers import RotatingFileHandler
from pathlib import Path

from platformdirs import user_log_dir


def configure_logging(log_dir: Path | None = None) -> Path | None:
    """Keep bounded diagnostic logs under the user's application data directory."""
    logger = logging.getLogger("orbit_wizard_blue")
    logger.setLevel(logging.INFO)
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()
    target_dir = log_dir or Path(os.environ.get("ORBIT_WIZARD_LOG_DIR") or user_log_dir("orbit-wizard-blue"))
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        path = target_dir / "orbit-wizard-blue.log"
        handler = RotatingFileHandler(path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.info("Application logging started")
        return path
    except OSError:
        logger.addHandler(logging.StreamHandler(sys.stderr))
        logger.exception("Could not create application log directory: %s", target_dir)
        return None


def _install_exception_hook(log_path: Path | None) -> None:
    def record_unhandled(exc_type, exc, tb):
        logging.getLogger("orbit_wizard_blue").critical("Unhandled application exception; log: %s",
                                                        log_path or "stderr", exc_info=(exc_type, exc, tb))
        traceback.print_exception(exc_type, exc, tb)

    sys.excepthook = record_unhandled


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
    versions = {"orbit-wizard-blue": result.provenance.get("app_version"),
                **result.provenance.get("libraries", {})}
    if any(not value or value == "unknown" for value in versions.values()):
        raise RuntimeError(f"Package metadata missing from bundle: {versions}")
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
    log_path = configure_logging()
    _install_exception_hook(log_path)
    from PySide6.QtWidgets import QApplication

    from orbit_wizard_blue.gui import MainWindow

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("orbit-wizard-blue")
        window = MainWindow()
        window.show()
        return app.exec()
    except Exception:
        logging.getLogger("orbit_wizard_blue").exception("Application startup failed; log: %s",
                                                         log_path or "stderr")
        raise


if __name__ == "__main__":
    raise SystemExit(main())
