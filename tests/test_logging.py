"""Diagnostic logs use a bounded, injectable directory."""

from __future__ import annotations

import logging
import sys

from orbit_wizard_blue.__main__ import _install_exception_hook, configure_logging
from orbit_wizard_blue.gui.workers import TaskWorker


def test_rotating_file_and_unhandled_traceback_use_temp_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("ORBIT_WIZARD_LOG_DIR", str(tmp_path))
    original_hook = sys.excepthook
    try:
        path = configure_logging()
        assert path == tmp_path / "orbit-wizard-blue.log"
        _install_exception_hook(path)
        try:
            raise ValueError("sample failure")
        except ValueError as exc:
            sys.excepthook(type(exc), exc, exc.__traceback__)
        assert "sample failure" in path.read_text(encoding="utf-8")
        assert "log:" in path.read_text(encoding="utf-8")
    finally:
        sys.excepthook = original_hook
        for handler in logging.getLogger("orbit_wizard_blue").handlers[:]:
            handler.close()
            logging.getLogger("orbit_wizard_blue").removeHandler(handler)


def test_worker_logs_exception_with_traceback(tmp_path):
    path = configure_logging(tmp_path)
    errors = []

    def fail(_progress, _cancel):
        raise RuntimeError("worker failure")

    worker = TaskWorker(fail)
    worker.failed.connect(errors.append)
    worker.run()
    assert errors and "worker failure" in errors[0]
    assert "RuntimeError: worker failure" in path.read_text(encoding="utf-8")
