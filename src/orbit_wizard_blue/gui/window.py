"""Main desktop window and synchronized sample playback."""

from __future__ import annotations

from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QDateTime, QThread, QTimeZone, QTimer, Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateTimeEdit, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QProgressBar, QPushButton, QSlider, QSpinBox, QSplitter, QTabWidget,
    QTableView, QVBoxLayout, QWidget,
)

from orbit_wizard_blue.data import DataService
from orbit_wizard_blue.models import DataSnapshot, OrbitRequest, OrbitResult

from .orbit_view import OrbitView
from .tables import OrbitTableModel
from .workers import TaskWorker


def _name(snapshot: DataSnapshot) -> str:
    return str(snapshot.payload.get("OBJECT_NAME") or snapshot.payload.get("OBJECT_ID") or "이름 없음")


def _id(snapshot: DataSnapshot) -> str:
    return str(snapshot.payload.get("NORAD_CAT_ID", ""))


class MainWindow(QMainWindow):
    def __init__(self, service: DataService | None = None):
        super().__init__()
        self.setWindowTitle("orbit-wizard-blue — 위성 궤도 분석")
        self.resize(1360, 860)
        self.service = service if service is not None else DataService()
        self.snapshot: DataSnapshot | None = None
        self.result: OrbitResult | None = None
        self._worker: TaskWorker | None = None
        self._thread: QThread | None = None
        self._pending_close = False
        self._sample_seconds: list[float] = []
        self._play_base = 0.0
        self._play_started = 0.0
        self._playing = False
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._play_tick)
        self._update_controls()

    def _build_ui(self) -> None:
        body = QWidget()
        self.setCentralWidget(body)
        outer = QVBoxLayout(body)
        split = QSplitter(Qt.Horizontal)
        outer.addWidget(split, 1)
        left = QWidget()
        left.setMaximumWidth(380)
        left_layout = QVBoxLayout(left)
        split.addWidget(left)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        split.addWidget(right)
        split.setStretchFactor(1, 1)

        source_box = QGroupBox("위성 자료")
        source = QVBoxLayout(source_box)
        search_row = QHBoxLayout()
        self.query = QLineEdit()
        self.query.setPlaceholderText("위성 이름 또는 NORAD 번호")
        self.query.returnPressed.connect(self.search)
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search)
        search_row.addWidget(self.query, 1)
        search_row.addWidget(self.search_button)
        source.addLayout(search_row)
        self.matches = QListWidget()
        self.matches.setMinimumHeight(150)
        self.matches.currentItemChanged.connect(self._select_satellite)
        source.addWidget(self.matches)
        self.refresh_button = QPushButton("자료 업데이트")
        self.refresh_button.clicked.connect(self.refresh_data)
        source.addWidget(self.refresh_button)
        self.source_status = QLabel("위성을 검색해 주세요.")
        self.source_status.setWordWrap(True)
        source.addWidget(self.source_status)
        left_layout.addWidget(source_box)

        request_box = QGroupBox("계산 구간 · UTC")
        form = QFormLayout(request_box)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        self.start_edit = QDateTimeEdit()
        self.end_edit = QDateTimeEdit()
        for edit in (self.start_edit, self.end_edit):
            edit.setTimeZone(QTimeZone.utc())
            edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss 'UTC'")
            edit.setCalendarPopup(True)
        self.start_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(now.timestamp()), QTimeZone.utc()))
        self.end_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int((now + timedelta(hours=24)).timestamp()),
                                                      QTimeZone.utc()))
        self.step_edit = QSpinBox()
        self.step_edit.setRange(1, 86400)
        self.step_edit.setValue(60)
        self.step_edit.setSuffix(" 초")
        form.addRow("시작", self.start_edit)
        form.addRow("종료", self.end_edit)
        form.addRow("간격", self.step_edit)
        left_layout.addWidget(request_box)

        self.calculate_button = QPushButton("궤도 계산")
        self.calculate_button.clicked.connect(self.calculate)
        left_layout.addWidget(self.calculate_button)
        self.cancel_button = QPushButton("작업 취소")
        self.cancel_button.clicked.connect(self.cancel_task)
        left_layout.addWidget(self.cancel_button)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        left_layout.addWidget(self.progress)
        self.task_status = QLabel("준비됨")
        self.task_status.setWordWrap(True)
        left_layout.addWidget(self.task_status)
        self.recompute_notice = QLabel("")
        self.recompute_notice.setWordWrap(True)
        left_layout.addWidget(self.recompute_notice)
        left_layout.addStretch()
        self.export_button = QPushButton("결과 CSV 내보내기")
        self.export_button.clicked.connect(self.export_result)
        left_layout.addWidget(self.export_button)

        self.tabs = QTabWidget()
        right_layout.addWidget(self.tabs, 1)
        view_page = QWidget()
        view_layout = QVBoxLayout(view_page)
        view_tools = QHBoxLayout()
        self.frame_combo = QComboBox()
        self.frame_combo.addItem("GCRS · 관성", "GCRS")
        self.frame_combo.addItem("ITRS · 지구 고정", "ITRS")
        self.frame_combo.currentIndexChanged.connect(self._change_frame)
        self.reset_camera_button = QPushButton("시점 초기화")
        self.fit_camera_button = QPushButton("궤도에 맞추기")
        view_tools.addWidget(QLabel("시점"))
        view_tools.addWidget(self.frame_combo)
        view_tools.addStretch()
        view_tools.addWidget(self.reset_camera_button)
        view_tools.addWidget(self.fit_camera_button)
        view_layout.addLayout(view_tools)
        self.orbit_view = OrbitView()
        view_layout.addWidget(self.orbit_view, 1)
        self.reset_camera_button.clicked.connect(self.orbit_view.reset_camera)
        self.fit_camera_button.clicked.connect(self.orbit_view.fit_camera)
        self.tabs.addTab(view_page, "3D 궤도")
        self.tables: list[QTableView] = []
        self.models: list[OrbitTableModel] = []
        for frame in ("TEME", "ITRS", "측지"):
            model = OrbitTableModel(frame, self)
            table = QTableView()
            table.setModel(model)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)
            table.setSortingEnabled(False)
            table.verticalHeader().setDefaultSectionSize(23)
            table.horizontalHeader().setStretchLastSection(True)
            table.selectionModel().currentRowChanged.connect(self._table_row_changed)
            self.tabs.addTab(table, frame)
            self.tables.append(table)
            self.models.append(model)

        playback = QHBoxLayout()
        self.play_button = QPushButton("▶ 재생")
        self.play_button.clicked.connect(self._toggle_play)
        self.reset_button = QPushButton("처음")
        self.reset_button.clicked.connect(self._reset_play)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self.set_sample_index)
        self.speed_combo = QComboBox()
        for speed in (1, 10, 60, 600):
            self.speed_combo.addItem(f"{speed}×", speed)
        self.speed_combo.setCurrentIndex(2)
        self._last_speed = 60
        self.speed_combo.currentIndexChanged.connect(self._speed_changed)
        playback.addWidget(self.play_button)
        playback.addWidget(self.reset_button)
        playback.addWidget(self.slider, 1)
        playback.addWidget(self.speed_combo)
        right_layout.addLayout(playback)
        self.sample_label = QLabel("계산 결과 없음")
        right_layout.addWidget(self.sample_label)

    def _start_task(self, label: str, task, on_success) -> None:
        if self._thread is not None:
            return
        self._pause()
        self.task_status.setText(label)
        self.progress.setValue(0)
        thread = QThread(self)
        worker = TaskWorker(task)
        worker.moveToThread(thread)
        self._thread, self._worker = thread, worker
        thread.started.connect(worker.run)
        worker.progress.connect(self._task_progress)
        worker.succeeded.connect(on_success)
        worker.failed.connect(self._task_failed)
        worker.cancelled.connect(lambda: self.task_status.setText("작업이 취소되었습니다."))
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(self._thread_finished)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._update_controls()

    def _thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._update_controls()
        if self._pending_close:
            QTimer.singleShot(0, self.close)

    def _task_progress(self, percent: int, message: str) -> None:
        self.progress.setValue(max(0, min(100, percent)))
        self.task_status.setText(message)

    def _task_failed(self, message: str) -> None:
        self.task_status.setText(f"오류: {message}")
        QMessageBox.warning(self, "작업 오류", message)

    def cancel_task(self) -> None:
        if self._worker is not None:
            self._worker.request_cancel()
            self.task_status.setText("취소 중…")

    def search(self) -> None:
        query = self.query.text().strip()
        if not query:
            self.task_status.setText("검색어를 입력해 주세요.")
            return
        self._start_task("위성 검색 중…", lambda progress, cancel: self.service.search_satellites(query, cancel=cancel),
                         self._show_matches)

    def _show_matches(self, snapshots: list[DataSnapshot]) -> None:
        self.matches.clear()
        self.snapshot = None
        for snapshot in snapshots:
            item = QListWidgetItem(f"{_name(snapshot)} · {_id(snapshot)}")
            item.setData(Qt.UserRole, snapshot)
            self.matches.addItem(item)
        self.task_status.setText(f"검색 결과 {len(snapshots)}개")
        if snapshots:
            self.matches.setCurrentRow(0)
        else:
            self.source_status.setText("검색 결과가 없습니다.")
        self._update_controls()

    def _select_satellite(self, current: QListWidgetItem | None, _previous) -> None:
        self.snapshot = current.data(Qt.UserRole) if current is not None else None
        self._show_source_status()
        self._update_controls()

    def _show_source_status(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            self.source_status.setText("위성을 선택해 주세요.")
            return
        age = "오래된 캐시" if snapshot.stale else "확인됨"
        self.source_status.setText(
            f"{age} · 요소시각 UTC: {snapshot.payload.get('EPOCH', '알 수 없음')}"
            f"\n확인 UTC: {snapshot.checked_at}\n수신 UTC: {snapshot.fetched_at}"
            f"\n출처: {snapshot.source_url}"
            + (f"\n주의: {snapshot.warning}" if snapshot.warning else "")
        )

    def refresh_data(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            self.task_status.setText("업데이트할 위성을 선택해 주세요.")
            return
        def task(progress, cancel):
            progress(5, "위성 자료 확인 중…")
            fresh = self.service.resolve_satellite(snapshot, force=True, cancel=cancel)
            progress(50, "지구 회전 자료 확인 중…")
            earth = self.service.get_earth_data(force=True, cancel=cancel)
            return fresh, earth

        self._start_task("자료 업데이트 중…", task, self._refresh_done)

    def _refresh_done(self, value) -> None:
        snapshot, earth = value
        self.snapshot = snapshot
        current = self.matches.currentItem()
        if current is not None:
            current.setData(Qt.UserRole, snapshot)
            current.setText(f"{_name(snapshot)} · {_id(snapshot)}")
        self._show_source_status()
        provider_wait = "next GP check" in snapshot.warning
        self.task_status.setText(("제공자 갱신 대기 중" if provider_wait else "자료 업데이트 완료")
                                 + (f" · {snapshot.warning}" if snapshot.warning else "")
                                 + (f" · {earth.warning}" if earth.warning else ""))
        if self.result is not None:
            old_earth = self.result.provenance.get("earth_data", {})
            earth_changed = any(
                earth.provenance.get(key, {}).get("sha256") != old_earth.get(key, {}).get("sha256")
                for key in ("iers", "leap_seconds")
            )
            if snapshot.sha256 != self.result.satellite.sha256 or earth_changed:
                self.recompute_notice.setText("자료가 업데이트되었습니다. 표시된 계산 결과는 이전 자료로 계산되었습니다. 새 결과를 보려면 다시 계산하세요.")

    def _date_utc(self, edit: QDateTimeEdit) -> datetime:
        return edit.dateTime().toPython().replace(tzinfo=timezone.utc)

    def calculate(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            self.task_status.setText("위성을 선택해 주세요.")
            return
        request = OrbitRequest(self._date_utc(self.start_edit), self._date_utc(self.end_edit), self.step_edit.value())
        if request.end_utc <= request.start_utc:
            QMessageBox.warning(self, "입력 오류", "종료 시각은 시작 시각보다 늦어야 합니다.")
            return

        def task(progress, cancel):
            from orbit_wizard_blue.orbit import compute_ephemeris

            progress(1, "선택 위성 자료 확인 중…")
            current_snapshot = self.service.resolve_satellite(snapshot, cancel=cancel)
            progress(2, "지구 회전 자료 확인 중…")
            earth = self.service.get_earth_data(cancel=cancel)
            return compute_ephemeris(current_snapshot, request, earth, progress=progress, cancel=cancel)

        self._start_task("궤도 계산 중…", task, self._calculation_done)

    def _calculation_done(self, result: OrbitResult) -> None:
        self.result = result
        self.snapshot = result.satellite
        current = self.matches.currentItem()
        if current is not None:
            current.setData(Qt.UserRole, self.snapshot)
        self._show_source_status()
        self._sample_seconds = [(datetime.fromisoformat(t.replace("Z", "+00:00"))
                                 - datetime.fromisoformat(result.times_utc[0].replace("Z", "+00:00"))).total_seconds()
                                for t in result.times_utc]
        for model in self.models:
            model.set_result(result)
        self.orbit_view.set_result(result)
        self.slider.setRange(0, max(0, len(result.times_utc) - 1))
        self.set_sample_index(0)
        self.recompute_notice.setText("")
        self.task_status.setText(f"계산 완료 · {len(result.times_utc):,}개 샘플"
                                 + (f" · 주의: {'; '.join(result.warnings)}" if result.warnings else ""))
        self.progress.setValue(100)
        self._update_controls()

    def export_result(self) -> None:
        result = self.result
        if result is None:
            return
        proposed = f"orbit-{_id(result.satellite)}.csv"
        chosen, _ = QFileDialog.getSaveFileName(self, "결과 CSV 저장", proposed, "CSV 파일 (*.csv)")
        if not chosen:
            return

        def task(progress, cancel):
            from orbit_wizard_blue.export import export_ephemeris

            progress(10, "CSV와 메타데이터 저장 중…")
            return export_ephemeris(result, Path(chosen))

        self._start_task("결과 저장 중…", task, self._export_done)

    def _export_done(self, paths) -> None:
        self.progress.setValue(100)
        self.task_status.setText(f"저장 완료: {paths[0].name}, {paths[1].name}")

    def _change_frame(self) -> None:
        self.orbit_view.set_frame(self.frame_combo.currentData())
        self.orbit_view.fit_camera()

    def _table_row_changed(self, current, _previous) -> None:
        if current.isValid() and current.row() != self.slider.value():
            self.slider.setValue(current.row())

    def set_sample_index(self, index: int, *, from_timer: bool = False) -> None:
        result = self.result
        if result is None or not result.times_utc:
            return
        index = max(0, min(index, len(result.times_utc) - 1))
        if self.slider.value() != index:
            self.slider.blockSignals(True)
            self.slider.setValue(index)
            self.slider.blockSignals(False)
        self.orbit_view.set_index(index)
        for table in self.tables:
            selection = table.selectionModel()
            if selection.currentIndex().row() != index:
                table.selectRow(index)
        self.sample_label.setText(f"{index + 1:,} / {len(result.times_utc):,} · {result.times_utc[index]} UTC")
        if self._playing and not from_timer:
            self._play_base = self._sample_seconds[index]
            self._play_started = monotonic()

    def _toggle_play(self) -> None:
        if self._playing:
            self._pause()
        elif self.result is not None and len(self._sample_seconds) > 1:
            if self.slider.value() >= len(self._sample_seconds) - 1:
                self.set_sample_index(0)
            self._play_base = self._sample_seconds[self.slider.value()]
            self._play_started = monotonic()
            self._playing = True
            self._timer.start()
            self.play_button.setText("⏸ 일시정지")

    def _pause(self) -> None:
        if self._playing:
            self._play_base += (monotonic() - self._play_started) * self.speed_combo.currentData()
        self._playing = False
        self._timer.stop() if hasattr(self, "_timer") else None
        self.play_button.setText("▶ 재생")

    def _reset_play(self) -> None:
        self._pause()
        self.set_sample_index(0)

    def _speed_changed(self) -> None:
        if self._playing:
            self._play_base += (monotonic() - self._play_started) * self._last_speed
            self._play_started = monotonic()
        self._last_speed = self.speed_combo.currentData()

    def _play_tick(self) -> None:
        if not self._sample_seconds:
            self._pause()
            return
        target = self._play_base + (monotonic() - self._play_started) * self.speed_combo.currentData()
        if target >= self._sample_seconds[-1]:
            self.set_sample_index(len(self._sample_seconds) - 1, from_timer=True)
            self._pause()
            return
        self.set_sample_index(max(0, bisect_right(self._sample_seconds, target) - 1), from_timer=True)

    def _update_controls(self) -> None:
        busy = self._thread is not None
        self.search_button.setEnabled(not busy)
        self.matches.setEnabled(not busy)
        self.query.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy and self.snapshot is not None)
        self.calculate_button.setEnabled(not busy and self.snapshot is not None)
        self.cancel_button.setEnabled(busy)
        self.export_button.setEnabled(not busy and self.result is not None)
        self.play_button.setEnabled(self.result is not None and len(self.result.times_utc) > 1)
        self.reset_button.setEnabled(self.result is not None)
        self.slider.setEnabled(self.result is not None)

    def closeEvent(self, event) -> None:
        if self._thread is not None:
            self._pending_close = True
            self.cancel_task()
            event.ignore()
            return
        self._pause()
        event.accept()
