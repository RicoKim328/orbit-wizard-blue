"""Offline equirectangular ground-track view using bundled coastlines."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from orbit_wizard_blue.ground_track import ground_track_plot
from orbit_wizard_blue.models import OrbitResult, ValidationError


@lru_cache(maxsize=1)
def coastline_points() -> tuple[np.ndarray, np.ndarray]:
    """Load bundled 1:110m coastlines as one pen path with NaN gaps."""
    path = files("orbit_wizard_blue").joinpath("assets", "ne_110m_coastline.geojson")
    data = json.loads(path.read_text(encoding="utf-8"))
    longitudes: list[float] = []
    latitudes: list[float] = []
    for feature in data["features"]:
        geometry = feature["geometry"]
        kind = geometry["type"]
        if kind == "LineString":
            paths = [geometry["coordinates"]]
        elif kind == "MultiLineString":
            paths = geometry["coordinates"]
        else:
            continue
        for coordinates in paths:
            previous = None
            for longitude, latitude, *_ in coordinates:
                longitude = (float(longitude) + 180.0) % 360.0 - 180.0
                if previous is not None and abs(longitude - previous) > 180:
                    longitudes.append(float("nan"))
                    latitudes.append(float("nan"))
                longitudes.append(longitude)
                latitudes.append(float(latitude))
                previous = longitude
            longitudes.append(float("nan"))
            latitudes.append(float("nan"))
    return np.asarray(longitudes), np.asarray(latitudes)


class GroundTrackView(QWidget):
    """World map and trajectory synchronized to an OrbitResult sample index."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result: OrbitResult | None = None
        self.index = 0
        self._track_available = False
        layout = QVBoxLayout(self)
        tools = QHBoxLayout()
        tools.addWidget(QLabel("경도/위도 평면 · Natural Earth 1:110m"))
        tools.addStretch()
        self.fit_button = QPushButton("전체 보기")
        self.fit_button.clicked.connect(self.fit_world)
        tools.addWidget(self.fit_button)
        layout.addLayout(tools)
        self.plot = pg.PlotWidget(background="#091324")
        self.plot.setLabel("bottom", "경도", units="°")
        self.plot.setLabel("left", "위도", units="°")
        self.plot.showGrid(x=True, y=True, alpha=0.17)
        # A locked aspect can crop longitude when the dock is taller than 2:1.
        # Keep the full geographic extent visible at every window size.
        self.plot.getViewBox().setAspectLocked(False)
        self.plot.getViewBox().setLimits(xMin=-180, xMax=180, yMin=-90, yMax=90)
        coast_lon, coast_lat = coastline_points()
        self.plot.plot(coast_lon, coast_lat, pen=pg.mkPen("#66849a", width=1), connect="finite")
        self.track = self.plot.plot([], [], pen=pg.mkPen("#ffbb55", width=2), connect="finite")
        self.marker = pg.ScatterPlotItem(size=12, pen=pg.mkPen("#f7eeee", width=1),
                                         brush=pg.mkBrush("#ff554f"))
        self.plot.addItem(self.marker)
        layout.addWidget(self.plot, 1)
        self.sample_label = QLabel("계산된 측지 자료가 없습니다.")
        layout.addWidget(self.sample_label)
        self.fit_world()

    def fit_world(self) -> None:
        self.plot.setXRange(-180, 180, padding=0)
        self.plot.setYRange(-90, 90, padding=0)

    def set_result(self, result: OrbitResult | None) -> None:
        self.result = result
        self.index = 0
        self._track_available = False
        if result is None or result.geodetic_deg_km is None:
            self.track.setData([], [])
            self.marker.setData([], [])
            self.sample_label.setText("측지 변환 자료가 없어 지상 궤적을 표시할 수 없습니다.")
            return
        try:
            coordinates = ground_track_plot(result.geodetic_deg_km)
        except ValidationError as exc:
            self.track.setData([], [])
            self.marker.setData([], [])
            self.sample_label.setText(f"지상 궤적을 표시할 수 없습니다: {exc}")
            return
        if coordinates is None:
            self.track.setData([], [])
            self.marker.setData([], [])
            self.sample_label.setText("측지 변환 자료가 없어 지상 궤적을 표시할 수 없습니다.")
            return
        self._track_available = True
        self.track.setData(*coordinates)
        self.set_index(0)

    def set_index(self, index: int) -> None:
        self.index = index
        result = self.result
        if not self._track_available or result is None or result.geodetic_deg_km is None or not result.times_utc:
            self.marker.setData([], [])
            return
        latitude, longitude, height = (float(value) for value in result.geodetic_deg_km[index])
        longitude = (longitude + 180.0) % 360.0 - 180.0
        self.marker.setData([longitude], [latitude])
        self.sample_label.setText(
            f"{result.times_utc[index]} UTC · 위도 {latitude:.6f}° · 경도 {longitude:.6f}° · 고도 {height:,.3f} km"
        )
