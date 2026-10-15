"""PyOpenGL Windows platform using Qt's software OpenGL library."""

from __future__ import annotations

import ctypes
import os
from pathlib import Path
import sys

from OpenGL.platform.baseplatform import lazy_property
from OpenGL.platform.win32 import Win32Platform


def _qt_software_library() -> str:
    configured = os.environ.get("QT_OPENGL_DLL")
    if configured:
        return configured
    import PySide6

    package = Path(PySide6.__file__).resolve().parent
    candidates = (
        package / "opengl32sw.dll",
        package / "Qt" / "bin" / "opengl32sw.dll",
        package / "Qt6" / "bin" / "opengl32sw.dll",
        package.parent / "opengl32sw.dll",
        Path(sys.executable).resolve().parent / "opengl32sw.dll",
    )
    for path in candidates:
        if path.is_file():
            return str(path)
    return "opengl32sw.dll"


class QtSoftwareWin32Platform(Win32Platform):
    """Route GL, WGL, extension lookup and context checks to one DLL."""

    @lazy_property
    def GL(self):
        path = _qt_software_library()
        try:
            return ctypes.WinDLL(path)
        except OSError as exc:
            raise ImportError(f"Qt software OpenGL library is unavailable: {path}") from exc
