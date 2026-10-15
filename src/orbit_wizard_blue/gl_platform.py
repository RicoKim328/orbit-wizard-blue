"""Choose the same Windows OpenGL implementation for Qt and PyOpenGL."""

from __future__ import annotations

import os
import sys


_PLUGIN_NAME = "orbit_qt_software"


def configure_pyopengl() -> None:
    """Register PyOpenGL's Qt software-DLL platform before importing OpenGL.GL.

    Qt's QT_OPENGL=software context belongs to opengl32sw.dll, while
    PyOpenGL's default Windows platform calls opengl32.dll. A context from
    one DLL is not current to the other DLL's WGL entry points.
    """
    if sys.platform != "win32":
        return
    # Qt's implicit fallback can switch to opengl32sw.dll after PyOpenGL has
    # already bound opengl32.dll. Keep the normal system GL path explicit.
    os.environ.setdefault("QT_OPENGL", "desktop")
    if os.environ["QT_OPENGL"].lower() != "software":
        return
    from OpenGL.plugins import PlatformPlugin

    if "OpenGL.platform" in sys.modules:
        from OpenGL import platform

        if platform.PLATFORM.__class__.__name__ != "QtSoftwareWin32Platform":
            raise RuntimeError("PyOpenGL was imported before Qt software OpenGL was configured")
        return
    if os.environ.get("PYOPENGL_PLATFORM") not in (None, _PLUGIN_NAME):
        raise RuntimeError("PYOPENGL_PLATFORM conflicts with QT_OPENGL=software")
    if PlatformPlugin.by_name(_PLUGIN_NAME) is None:
        PlatformPlugin(_PLUGIN_NAME, "orbit_wizard_blue.gl_software_win32.QtSoftwareWin32Platform")
    os.environ["PYOPENGL_PLATFORM"] = _PLUGIN_NAME
