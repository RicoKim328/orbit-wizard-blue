"""Run network and propagation work outside the Qt GUI thread."""

from __future__ import annotations

from threading import Event
from typing import Callable

from PySide6.QtCore import QObject, Signal, Slot

from orbit_wizard_blue.models import CancelledError


class TaskWorker(QObject):
    progress = Signal(int, str)
    succeeded = Signal(object)
    failed = Signal(str)
    cancelled = Signal()
    finished = Signal()

    def __init__(self, task: Callable[[Callable[[int, str], None], Callable[[], bool]], object]):
        super().__init__()
        self._task = task
        self._cancel = Event()

    def request_cancel(self) -> None:
        self._cancel.set()

    @Slot()
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
            if self._cancel.is_set():
                self.cancelled.emit()
            else:
                self.failed.emit(f"{type(exc).__name__}: {exc}")
        finally:
            self.finished.emit()
