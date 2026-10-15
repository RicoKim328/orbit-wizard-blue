"""Embedded OpenGL Earth and sampled orbit view."""

from __future__ import annotations

import os

import numpy as np
from PySide6.QtCore import QTimer, Signal
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from orbit_wizard_blue.models import OrbitResult
from orbit_wizard_blue.gl_platform import configure_pyopengl


EARTH_RADIUS_KM = 6378.137
EARTH_POLAR_RADIUS_KM = 6356.752314245


class OrbitView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result: OrbitResult | None = None
        self.index = 0
        self.frame = "GCRS"
        self.available = False
        self._earth_items = []
        self._layout = QVBoxLayout(self)
        if os.environ.get("ORBIT_WIZARD_DISABLE_3D") == "1":
            self._layout.addWidget(QLabel("3D 표시가 비활성화되었습니다."))
            return
        try:
            configure_pyopengl()
            import pyqtgraph.opengl as gl
            from pyqtgraph import Vector

            class SafeGLViewWidget(gl.GLViewWidget):
                failed = Signal(str)

                def initializeGL(self):
                    try:
                        super().initializeGL()
                    except Exception as exc:
                        self.failed.emit(str(exc))

            self._gl = gl
            self._vector = Vector
            self.view = SafeGLViewWidget()
            self.view.failed.connect(self._disable_3d)
            self.view.setBackgroundColor((9, 19, 36))
            self._layout.addWidget(self.view)
            self.available = True
            self._build_earth()
            self.reset_camera()
        except Exception as exc:
            self.available = False
            self._layout.addWidget(QLabel(f"3D 표시를 시작할 수 없습니다: {exc}"))

    def showEvent(self, event):
        super().showEvent(event)
        if self.available:
            QTimer.singleShot(0, self._check_context)

    def _check_context(self) -> None:
        if self.available and self.isVisible() and not self.view.isValid():
            self._disable_3d("OpenGL 컨텍스트를 사용할 수 없습니다.")

    def _disable_3d(self, reason: str) -> None:
        if not self.available:
            return
        self.available = False
        self._layout.removeWidget(self.view)
        self.view.hide()
        self.view.deleteLater()
        self._layout.addWidget(QLabel(f"3D 표시를 사용할 수 없습니다: {reason}"))

    @staticmethod
    def _surface(lat_deg, lon_deg):
        lat = np.deg2rad(lat_deg)
        lon = np.deg2rad(lon_deg)
        eccentricity_sq = 1 - (EARTH_POLAR_RADIUS_KM / EARTH_RADIUS_KM) ** 2
        prime_vertical = EARTH_RADIUS_KM / np.sqrt(1 - eccentricity_sq * np.sin(lat) ** 2)
        return np.stack((
            prime_vertical * np.cos(lat) * np.cos(lon),
            prime_vertical * np.cos(lat) * np.sin(lon),
            prime_vertical * (1 - eccentricity_sq) * np.sin(lat),
        ), axis=-1)

    def _build_earth(self) -> None:
        gl = self._gl
        # Ellipsoid mesh in ITRS. Latitude/longitude lines show its rotation in GCRS.
        lats = np.linspace(-90, 90, 37)
        lons = np.linspace(-180, 180, 73)
        vertices = self._surface(*np.meshgrid(lats, lons, indexing="ij"))
        faces = []
        for i in range(len(lats) - 1):
            for j in range(len(lons) - 1):
                a = i * len(lons) + j
                faces.extend(((a, a + len(lons), a + 1), (a + 1, a + len(lons), a + len(lons) + 1)))
        mesh = gl.MeshData(vertexes=vertices.reshape(-1, 3), faces=np.asarray(faces))
        earth = gl.GLMeshItem(meshdata=mesh, smooth=False, color=(0.055, 0.14, 0.29, 1.0),
                              drawEdges=False, shader="shaded", glOptions="opaque")
        self.view.addItem(earth)
        self._earth_items.append(earth)
        for lat in range(-60, 90, 30):
            pts = self._surface(np.full(181, lat), np.linspace(-180, 180, 181)) * 1.001
            line = gl.GLLinePlotItem(pos=pts, color=(0.36, 0.52, 0.66, 1.0), width=1, antialias=True,
                                     glOptions="opaque")
            self.view.addItem(line)
            self._earth_items.append(line)
        for lon in range(-180, 180, 30):
            pts = self._surface(np.linspace(-90, 90, 181), np.full(181, lon)) * 1.001
            line = gl.GLLinePlotItem(pos=pts, color=(0.36, 0.52, 0.66, 1.0), width=1, antialias=True,
                                     glOptions="opaque")
            self.view.addItem(line)
            self._earth_items.append(line)
        self.trajectory = gl.GLLinePlotItem(color=(1.0, 0.67, 0.16, 1.0), width=2.5,
                                            antialias=True, glOptions="opaque")
        self.marker = gl.GLScatterPlotItem(color=(1.0, 0.22, 0.19, 1.0), size=13, pxMode=True)
        self.view.addItem(self.trajectory)
        self.view.addItem(self.marker)
        for label, endpoint, color in (("X", (EARTH_RADIUS_KM * 1.5, 0, 0), (1, 0.25, 0.25, 1)),
                                      ("Y", (0, EARTH_RADIUS_KM * 1.5, 0), (0.3, 1, 0.3, 1)),
                                      ("Z", (0, 0, EARTH_RADIUS_KM * 1.5), (0.3, 0.55, 1, 1))):
            self.view.addItem(gl.GLLinePlotItem(pos=np.asarray(((0, 0, 0), endpoint), dtype=float),
                                                color=color, width=2, antialias=True, glOptions="opaque"))
            self.view.addItem(gl.GLTextItem(pos=np.asarray(endpoint) * 1.045,
                                            text=label, color=[int(channel * 255) for channel in color]))

    def set_result(self, result: OrbitResult | None) -> None:
        self.result = result
        self.index = 0
        self._update_geometry()
        self.fit_camera()

    def set_frame(self, frame: str) -> None:
        self.frame = frame
        self._update_geometry()

    def set_index(self, index: int) -> None:
        self.index = index
        self._update_marker_and_earth()

    def _update_geometry(self) -> None:
        if not self.available:
            return
        data = None
        if self.result is not None:
            data = self.result.gcrs_position_km if self.frame == "GCRS" else self.result.itrs_position_km
        self.trajectory.setData(pos=np.asarray(data) if data is not None else np.empty((0, 3)))
        self._update_marker_and_earth()

    def _update_marker_and_earth(self) -> None:
        if not self.available:
            return
        data = None
        if self.result is not None:
            data = self.result.gcrs_position_km if self.frame == "GCRS" else self.result.itrs_position_km
        if data is not None and len(data):
            self.marker.setData(pos=np.asarray(data[self.index:self.index + 1]))
        else:
            self.marker.setData(pos=np.empty((0, 3)))
        from PySide6.QtGui import QMatrix4x4

        matrix = QMatrix4x4()
        if self.frame == "GCRS" and self.result is not None and self.result.earth_rotation is not None:
            rotation = self.result.earth_rotation[self.index]
            # QMatrix4x4 constructor consumes row-major values.
            matrix = QMatrix4x4(*(
                float(rotation[0, 0]), float(rotation[0, 1]), float(rotation[0, 2]), 0.0,
                float(rotation[1, 0]), float(rotation[1, 1]), float(rotation[1, 2]), 0.0,
                float(rotation[2, 0]), float(rotation[2, 1]), float(rotation[2, 2]), 0.0,
                0.0, 0.0, 0.0, 1.0,
            ))
        for item in self._earth_items:
            item.resetTransform()
            item.applyTransform(matrix, local=False)

    def reset_camera(self) -> None:
        if self.available:
            self.view.setCameraPosition(pos=self._vector(0, 0, 0), distance=EARTH_RADIUS_KM * 4.2,
                                        elevation=24, azimuth=38)

    def fit_camera(self) -> None:
        if not self.available or self.result is None:
            return
        data = self.result.gcrs_position_km if self.frame == "GCRS" else self.result.itrs_position_km
        if data is None or len(data) == 0:
            return
        finite = np.asarray(data)[np.isfinite(data).all(axis=1)]
        radius = max(EARTH_RADIUS_KM, float(np.linalg.norm(finite, axis=1).max())) if len(finite) else EARTH_RADIUS_KM
        self.view.setCameraPosition(pos=self._vector(0, 0, 0), distance=radius * 2.8)
