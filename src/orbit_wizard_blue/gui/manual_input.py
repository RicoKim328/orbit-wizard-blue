"""Direct GCRS initial state and force-model controls."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from PySide6.QtCore import QDateTime, QTimeZone, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateTimeEdit, QDoubleSpinBox, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QScrollArea, QVBoxLayout, QWidget,
)


def _number(value: float, lower: float, upper: float, suffix: str, decimals: int = 8) -> QDoubleSpinBox:
    edit = QDoubleSpinBox()
    edit.setRange(lower, upper)
    edit.setDecimals(decimals)
    edit.setValue(value)
    edit.setSuffix(suffix)
    edit.setKeyboardTracking(False)
    return edit


def _utc_edit(value: datetime) -> QDateTimeEdit:
    edit = QDateTimeEdit()
    edit.setTimeZone(QTimeZone.utc())
    edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss 'UTC'")
    edit.setCalendarPopup(True)
    edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(value.timestamp()), QTimeZone.utc()))
    return edit


class ManualInputWidget(QScrollArea):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        body = QWidget()
        self.setWidget(body)
        layout = QVBoxLayout(body)
        self.name_edit = QLineEdit("수동 궤도")
        self.name_edit.setPlaceholderText("결과에 표시할 이름")
        epoch = datetime.now(timezone.utc).replace(microsecond=0)
        self.epoch_edit = _utc_edit(epoch)
        self.state_kind = QComboBox()
        self.state_kind.addItem("Kepler 6요소", "elements")
        self.state_kind.addItem("GCRS 위치·속도", "cartesian")
        setup = QFormLayout()
        setup.addRow("이름", self.name_edit)
        setup.addRow("요소시각", self.epoch_edit)
        setup.addRow("입력 형식", self.state_kind)
        layout.addLayout(setup)

        self.elements_group = QGroupBox("Kepler 6요소 · 요소시각의 GCRS")
        elements = QFormLayout(self.elements_group)
        self.element_edits = {
            "a_km": _number(7000, 1, 1e9, " km", 5),
            "e": _number(0.001, 0, 0.99999999, "", 8),
            "i_deg": _number(51.6, 0, 180, " °", 6),
            "raan_deg": _number(0, 0, 359.999999, " °", 6),
            "argp_deg": _number(0, 0, 359.999999, " °", 6),
            "true_anomaly_deg": _number(0, 0, 359.999999, " °", 6),
        }
        for label, key in (("장반경 a", "a_km"), ("이심률 e", "e"), ("경사각 i", "i_deg"),
                           ("승교점 적경 Ω", "raan_deg"), ("근지점 편각 ω", "argp_deg"),
                           ("진근점 이각 ν", "true_anomaly_deg")):
            elements.addRow(label, self.element_edits[key])
        layout.addWidget(self.elements_group)

        self.cartesian_group = QGroupBox("GCRS 상태벡터 · 요소시각")
        cartesian = QFormLayout(self.cartesian_group)
        self.position_edits = [_number(7000 if axis == 0 else 0, -1e9, 1e9, " km", 6)
                               for axis in range(3)]
        self.velocity_edits = [_number(7.5 if axis == 1 else 0, -1e4, 1e4, " km/s", 8)
                               for axis in range(3)]
        for axis, name in enumerate("XYZ"):
            cartesian.addRow(f"{name} 위치", self.position_edits[axis])
        for axis, name in enumerate("XYZ"):
            cartesian.addRow(f"V{name.lower()} 속도", self.velocity_edits[axis])
        self.cartesian_group.hide()
        layout.addWidget(self.cartesian_group)

        gravity = QFormLayout()
        self.gravity_combo = QComboBox()
        self.gravity_combo.addItem("J2 · 지구 편평도 근사 (기본)", "J2")
        self.gravity_combo.addItem("이체 · 구형 지구", "two_body")
        gravity.addRow("중력 모델", self.gravity_combo)
        layout.addLayout(gravity)

        self.accel_check = QCheckBox("추가 일정 가속도 적용")
        layout.addWidget(self.accel_check)
        self.accel_group = QGroupBox("추가 가속도 · 활성 UTC 구간")
        accel = QFormLayout(self.accel_group)
        self.accel_frame = QComboBox()
        self.accel_frame.addItem("GCRS 고정 축", "GCRS")
        self.accel_frame.addItem("RTN 궤도 축", "RTN")
        self.accel_frame.setToolTip("RTN: R=r/|r|, N=(r×v)/|r×v|, T=N×R. T는 편심 궤도의 속도 방향과 다를 수 있습니다.")
        accel.addRow("기준 축", self.accel_frame)
        self.accel_edits = [_number(0, -1e5, 1e5, " m/s²", 9) for _ in range(3)]
        self.accel_labels = []
        for axis, name in enumerate("XYZ"):
            label = QLabel(f"{name} 성분")
            self.accel_labels.append(label)
            accel.addRow(label, self.accel_edits[axis])
        self.accel_start = _utc_edit(epoch)
        self.accel_end = _utc_edit(epoch + timedelta(hours=1))
        self._previous_epoch = epoch
        accel.addRow("시작", self.accel_start)
        accel.addRow("끝", self.accel_end)
        layout.addWidget(self.accel_group)
        self.accel_group.hide()
        note = QLabel("입력은 GCRS 관성 좌표계입니다. 계산 시작은 요소시각으로 고정됩니다.")
        note.setWordWrap(True)
        layout.addWidget(note)
        layout.addStretch()

        self.name_edit.textChanged.connect(self.changed)
        self.epoch_edit.dateTimeChanged.connect(self._epoch_changed)
        self.state_kind.currentIndexChanged.connect(self._mode_changed)
        self.gravity_combo.currentIndexChanged.connect(self.changed)
        self.accel_check.toggled.connect(self._accel_toggled)
        self.accel_frame.currentIndexChanged.connect(self._accel_frame_changed)
        for edit in (*self.element_edits.values(), *self.position_edits, *self.velocity_edits, *self.accel_edits):
            edit.valueChanged.connect(self.changed)
        self.accel_start.dateTimeChanged.connect(self.changed)
        self.accel_end.dateTimeChanged.connect(self.changed)

    def _mode_changed(self) -> None:
        elements = self.state_kind.currentData() == "elements"
        self.elements_group.setVisible(elements)
        self.cartesian_group.setVisible(not elements)
        self.changed.emit()

    def _accel_toggled(self, enabled: bool) -> None:
        self.accel_group.setVisible(enabled)
        self.changed.emit()

    def _accel_frame_changed(self) -> None:
        if self.accel_frame.currentData() == "RTN":
            names = ("R · 방사", "T · 궤도 접선", "N · 궤도 법선")
        else:
            names = ("X · GCRS", "Y · GCRS", "Z · GCRS")
        for label, name in zip(self.accel_labels, names):
            label.setText(name)
        self.changed.emit()

    def _epoch_changed(self) -> None:
        epoch = self.epoch_utc()
        if (self.accel_start.dateTime().toPython().replace(tzinfo=timezone.utc) == self._previous_epoch
                and self.accel_end.dateTime().toPython().replace(tzinfo=timezone.utc)
                == self._previous_epoch + timedelta(hours=1)):
            self.accel_start.blockSignals(True)
            self.accel_end.blockSignals(True)
            self.accel_start.setDateTime(QDateTime.fromSecsSinceEpoch(int(epoch.timestamp()), QTimeZone.utc()))
            self.accel_end.setDateTime(QDateTime.fromSecsSinceEpoch(
                int((epoch + timedelta(hours=1)).timestamp()), QTimeZone.utc()))
            self.accel_start.blockSignals(False)
            self.accel_end.blockSignals(False)
        self._previous_epoch = epoch
        self.changed.emit()

    def epoch_utc(self) -> datetime:
        return self.epoch_edit.dateTime().toPython().replace(tzinfo=timezone.utc)

    def build_input(self):
        from orbit_wizard_blue.manual import ConstantAcceleration, KeplerianElements, ManualOrbitInput

        values = {key: edit.value() for key, edit in self.element_edits.items()}
        elements = KeplerianElements(**values) if self.state_kind.currentData() == "elements" else None
        position = tuple(edit.value() for edit in self.position_edits) if elements is None else None
        velocity = tuple(edit.value() for edit in self.velocity_edits) if elements is None else None
        acceleration = None
        if self.accel_check.isChecked():
            acceleration = ConstantAcceleration(
                vector_m_s2=tuple(edit.value() for edit in self.accel_edits),
                frame=self.accel_frame.currentData(),
                start_utc=self.accel_start.dateTime().toPython().replace(tzinfo=timezone.utc),
                end_utc=self.accel_end.dateTime().toPython().replace(tzinfo=timezone.utc),
            )
        return ManualOrbitInput(
            name=self.name_edit.text().strip(), epoch_utc=self.epoch_utc(), elements=elements,
            position_km=position, velocity_km_s=velocity,
            gravity_model=self.gravity_combo.currentData(), acceleration=acceleration,
        )
