"""Lazy Qt views over immutable orbit arrays."""

from __future__ import annotations

import math

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from orbit_wizard_blue.models import OrbitResult


class OrbitTableModel(QAbstractTableModel):
    def __init__(self, frame: str, parent=None):
        super().__init__(parent)
        self.frame = frame
        self.result: OrbitResult | None = None
        suffix = "위치 (km)" if frame != "측지" else "측지 좌표"
        if frame == "측지":
            self.headers = ("UTC", "위도 (°)", "경도 (°)", "고도 (km)")
        else:
            self.headers = (
                "UTC", f"X {suffix}", f"Y {suffix}", f"Z {suffix}",
                "Vx (km/s)", "Vy (km/s)", "Vz (km/s)",
            )

    def set_result(self, result: OrbitResult | None) -> None:
        self.beginResetModel()
        self.result = result
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() or self.result is None else len(self.result.times_utc)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        return self.headers[section] if orientation == Qt.Horizontal else str(section + 1)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or self.result is None or role not in (Qt.DisplayRole, Qt.TextAlignmentRole):
            return None
        if role == Qt.TextAlignmentRole:
            return int(Qt.AlignVCenter | (Qt.AlignLeft if index.column() == 0 else Qt.AlignRight))
        row, col = index.row(), index.column()
        if col == 0:
            return self.result.times_utc[row]
        if self.frame == "측지":
            array = self.result.geodetic_deg_km
        elif self.frame == "TEME":
            array = self.result.teme_position_km if col < 4 else self.result.teme_velocity_km_s
        else:
            array = self.result.itrs_position_km if col < 4 else self.result.itrs_velocity_km_s
        if array is None:
            return "—"
        value = float(array[row, (col - 1) % 3])
        return f"{value:,.6f}" if math.isfinite(value) else "—"
