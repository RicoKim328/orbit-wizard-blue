"""Cancellation-aware per-key locks shared by threads and app processes."""

from __future__ import annotations

from contextlib import contextmanager
import errno
import os
from pathlib import Path
import threading
import time
from typing import Callable, Iterator


_POLL_SECONDS = 0.05


@contextmanager
def thread_lock(
    lock: threading.Lock,
    check_cancel: Callable[[], None],
    on_wait: Callable[[], None] | None = None,
) -> Iterator[None]:
    check_cancel()
    if not lock.acquire(blocking=False):
        if on_wait is not None:
            on_wait()
        while True:
            check_cancel()
            if lock.acquire(timeout=_POLL_SECONDS):
                break
    try:
        yield
    finally:
        lock.release()


@contextmanager
def process_lock(
    path: Path,
    check_cancel: Callable[[], None],
    on_wait: Callable[[], None] | None = None,
) -> Iterator[None]:
    """Hold an OS file lock until the cache transaction completes.

    The file stays in the cache; the kernel releases its lock on process death.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"\0")
            stream.flush()
        if os.name == "nt":
            import msvcrt

            def acquire() -> None:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)

            def release() -> None:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            def acquire() -> None:
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            def release() -> None:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

        announced = False
        while True:
            check_cancel()
            try:
                acquire()
                break
            except OSError as exc:
                if exc.errno not in (errno.EACCES, errno.EAGAIN):
                    raise
                if not announced and on_wait is not None:
                    on_wait()
                    announced = True
                time.sleep(_POLL_SECONDS)
        try:
            yield
        finally:
            release()
