"""Run cancellable data and propagation tasks in a bounded Qt thread."""

from __future__ import annotations

import logging
from threading import Event
from typing import Callable

from PySide6.QtCore import QThread, Signal

from orbit_wizard_blue.models import CancelledError


class TaskWorker(QThread):
    progress = Signal(int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    def __init__(self, task: Callable[[Callable[[int, str], None], Callable[[], bool]], object], parent=None):
        super().__init__(parent)
        self._task = task
        self._cancel = Event()

    def request_cancel(self) -> None:
        self._cancel.set()

    def run(self) -> None:
        try:
            result = self._task(self.progress.emit, self._cancel.is_set)
            if self._cancel.is_set():
                self.cancelled.emit()
            else:
                self.succeeded.emit(result)
        except CancelledError:
            self.cancelled.emit()
        except Exception as exc:
            logging.getLogger("orbit_wizard_blue").exception("Background task failed")
            if self._cancel.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(f"{type(exc).__name__}: {exc}")
