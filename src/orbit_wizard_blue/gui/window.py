"""Main desktop window and synchronized sample playback."""

from __future__ import annotations

from bisect import bisect_right
from datetime import datetime, timedelta, timezone
from pathlib import Path
from time import monotonic

from PySide6.QtCore import QDateTime, QTimeZone, QTimer, Qt, Slot
from PySide6.QtWidgets import (
    QAbstractItemView, QComboBox, QDateTimeEdit, QDialog, QFileDialog, QFormLayout,
    QGroupBox, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
    QMessageBox, QPlainTextEdit, QProgressBar, QPushButton, QSlider, QSpinBox, QSplitter, QTabWidget,
    QTableView, QVBoxLayout, QWidget,
)

from orbit_wizard_blue.data import DataService
from orbit_wizard_blue.local_data import LocalDataService
from orbit_wizard_blue.models import CancelledError, DataSnapshot, EarthData, OrbitRequest, OrbitResult, ValidationError
from orbit_wizard_blue.user_store import FavoriteEntry, RecentEntry, UserStore

from .orbit_view import OrbitView
from .ground_track_view import GroundTrackView
from .manual_input import ManualInputWidget
from .tables import OrbitTableModel, configure_table_columns
from .workers import TaskWorker


def _name(snapshot: DataSnapshot) -> str:
    return str(snapshot.payload.get("OBJECT_NAME") or snapshot.payload.get("OBJECT_ID") or "이름 없음")


def _id(snapshot: DataSnapshot) -> str:
    return str(snapshot.payload.get("NORAD_CAT_ID", ""))


def _match_label(snapshot: DataSnapshot) -> str:
    epoch = str(snapshot.payload.get("EPOCH") or "시각 알 수 없음")
    kind = "로컬" if snapshot.source_kind == "local" else "온라인"
    return f"{_name(snapshot)} · NORAD {_id(snapshot)} · {epoch} · {kind}"


class MainWindow(QMainWindow):
    def __init__(self, service: DataService | None = None, *,
                 local_service: LocalDataService | None = None,
                 store: UserStore | None = None,
                 user_data_dir: Path | None = None):
        super().__init__()
        self.setWindowTitle("orbit-wizard-blue — 위성 궤도 분석")
        self.resize(1360, 860)
        self.service = service if service is not None else DataService()
        self.local_service = local_service if local_service is not None else LocalDataService(user_data_dir)
        self.store = store if store is not None else UserStore(user_data_dir)
        self.snapshot: DataSnapshot | None = None
        self.result: OrbitResult | None = None
        self.current_earth_data: EarthData | None = None
        self._thread: TaskWorker | None = None
        self._on_success = None
        self._pending_close = False
        self._sample_seconds: list[float] = []
        self._play_base = 0.0
        self._play_started = 0.0
        self._playing = False
        self._catalog_start: datetime | None = None
        self._build_ui()
        self._load_user_lists()
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
        self.search_widget = QWidget()
        search_row = QHBoxLayout(self.search_widget)
        search_row.setContentsMargins(0, 0, 0, 0)
        self.query = QLineEdit()
        self.query.setPlaceholderText("위성 이름 또는 NORAD 번호")
        self.query.returnPressed.connect(self.search)
        self.search_button = QPushButton("검색")
        self.search_button.clicked.connect(self.search)
        search_row.addWidget(self.query, 1)
        search_row.addWidget(self.search_button)
        source.addWidget(self.search_widget)
        self.import_button = QPushButton("로컬 GP JSON/TLE 파일 열기…")
        self.import_button.clicked.connect(self.import_file)
        source.addWidget(self.import_button)
        self.source_tabs = QTabWidget()
        self.matches = QListWidget()
        self.matches.setMinimumHeight(150)
        self.matches.currentItemChanged.connect(self._select_satellite)
        self.source_tabs.addTab(self.matches, "검색·파일")
        recent_page = QWidget()
        recent_layout = QVBoxLayout(recent_page)
        self.recent_list = QListWidget()
        self.recent_list.itemActivated.connect(self._open_recent)
        self.recent_list.currentItemChanged.connect(self._update_controls)
        recent_layout.addWidget(self.recent_list)
        recent_actions = QHBoxLayout()
        self.remove_recent_button = QPushButton("선택 삭제")
        self.remove_recent_button.clicked.connect(self.remove_recent)
        self.clear_recent_button = QPushButton("전체 지우기")
        self.clear_recent_button.clicked.connect(self.clear_recent)
        recent_actions.addWidget(self.remove_recent_button)
        recent_actions.addWidget(self.clear_recent_button)
        recent_layout.addLayout(recent_actions)
        self.source_tabs.addTab(recent_page, "최근")
        favorite_page = QWidget()
        favorite_layout = QVBoxLayout(favorite_page)
        self.favorite_list = QListWidget()
        self.favorite_list.itemActivated.connect(self._open_favorite)
        self.favorite_list.currentItemChanged.connect(self._update_controls)
        favorite_layout.addWidget(self.favorite_list)
        self.remove_favorite_button = QPushButton("선택 즐겨찾기 삭제")
        self.remove_favorite_button.clicked.connect(self.remove_selected_favorite)
        favorite_layout.addWidget(self.remove_favorite_button)
        self.source_tabs.addTab(favorite_page, "즐겨찾기")
        self.manual_input = ManualInputWidget()
        self.manual_input.changed.connect(self._manual_changed)
        self.source_tabs.addTab(self.manual_input, "직접 입력")
        self.source_tabs.currentChanged.connect(self._source_tab_changed)
        source.addWidget(self.source_tabs)
        self.favorite_button = QPushButton("선택 위성 즐겨찾기 추가")
        self.favorite_button.clicked.connect(self.toggle_favorite)
        source.addWidget(self.favorite_button)
        self.refresh_button = QPushButton("자료 업데이트")
        self.refresh_button.clicked.connect(self.refresh_data)
        source.addWidget(self.refresh_button)
        self.data_status_button = QPushButton("자료 상태…")
        self.data_status_button.clicked.connect(self.show_data_status)
        source.addWidget(self.data_status_button)
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
        self.start_edit.dateTimeChanged.connect(self._update_result_mismatch)
        self.end_edit.dateTimeChanged.connect(self._update_result_mismatch)
        self.step_edit.valueChanged.connect(self._update_result_mismatch)
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
        self.ground_track_view = GroundTrackView()
        self.tabs.addTab(self.ground_track_view, "지상 궤적")
        self.tables: list[QTableView] = []
        self.models: list[OrbitTableModel] = []
        for frame in ("TEME", "ITRS", "GCRS", "측지"):
            model = OrbitTableModel(frame, self)
            table = QTableView()
            table.setModel(model)
            table.setSelectionBehavior(QAbstractItemView.SelectRows)
            table.setSelectionMode(QAbstractItemView.SingleSelection)
            table.setSortingEnabled(False)
            table.verticalHeader().setDefaultSectionSize(23)
            configure_table_columns(table, frame)
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
        self.result_summary = QLabel("계산 결과가 없습니다.")
        self.result_summary.setWordWrap(True)
        self.result_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        right_layout.addWidget(self.result_summary)

    def _manual_active(self) -> bool:
        return self.source_tabs.currentWidget() is self.manual_input

    def _source_tab_changed(self) -> None:
        manual = self._manual_active()
        self.search_widget.setVisible(not manual)
        self.import_button.setVisible(not manual)
        self.favorite_button.setVisible(not manual)
        if manual:
            self._catalog_start = self._date_utc(self.start_edit)
            self.start_edit.setReadOnly(True)
            self.start_edit.setEnabled(False)
            self._manual_changed()
        elif self._catalog_start is not None:
            self.start_edit.setReadOnly(False)
            self.start_edit.setEnabled(True)
            self.start_edit.setDateTime(QDateTime.fromSecsSinceEpoch(
                int(self._catalog_start.timestamp()), QTimeZone.utc()))
            self._catalog_start = None
            current = self.matches.currentItem()
            self.snapshot = current.data(Qt.UserRole) if current is not None else None
            self._show_source_status()
            self._update_controls()
            self._update_result_mismatch()

    def _manual_changed(self) -> None:
        if not self._manual_active():
            return
        from orbit_wizard_blue.manual import manual_snapshot

        epoch = self.manual_input.epoch_utc()
        self.start_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(epoch.timestamp()), QTimeZone.utc()))
        try:
            manual = self.manual_input.build_input()
            self.snapshot = manual_snapshot(manual)
        except (ValidationError, ValueError, TypeError):
            self.snapshot = None
        self._show_source_status()
        self._update_controls()
        self._update_result_mismatch()

    def _start_task(self, label: str, task, on_success) -> None:
        if self._thread is not None:
            return
        self._pause()
        self.task_status.setText(label)
        self.progress.setValue(0)
        thread = TaskWorker(task, self)
        self._thread = thread
        self._on_success = on_success
        thread.progress.connect(self._task_progress, Qt.QueuedConnection)
        thread.succeeded.connect(self._task_succeeded, Qt.QueuedConnection)
        thread.failed.connect(self._task_failed, Qt.QueuedConnection)
        thread.cancelled.connect(self._task_cancelled, Qt.QueuedConnection)
        thread.finished.connect(self._thread_finished, Qt.QueuedConnection)
        thread.finished.connect(thread.deleteLater)
        thread.start()
        self._update_controls()
        self._update_result_mismatch()

    @Slot()
    def _thread_finished(self) -> None:
        thread = self._thread
        if thread is not None:
            thread.wait()
        self._thread = None
        self._on_success = None
        self._update_controls()
        if self._pending_close:
            QTimer.singleShot(0, self.close)

    @Slot(object)
    def _task_succeeded(self, value) -> None:
        if self._on_success is not None:
            self._on_success(value)

    @Slot(int, str)
    def _task_progress(self, percent: int, message: str) -> None:
        self.progress.setValue(max(0, min(100, percent)))
        self.task_status.setText(message)

    @Slot(str)
    def _task_failed(self, message: str) -> None:
        self.task_status.setText(f"오류: {message}")
        QMessageBox.warning(self, "작업 오류", message)

    @Slot()
    def _task_cancelled(self) -> None:
        self.task_status.setText("작업이 취소되었습니다.")

    def cancel_task(self) -> None:
        if self._thread is not None:
            self._thread.request_cancel()
            self.task_status.setText("취소 중…")

    def search(self) -> None:
        query = self.query.text().strip()
        if not query:
            self.task_status.setText("검색어를 입력해 주세요.")
            return
        def task(progress, cancel):
            return self.service.search_satellites(
                query, cancel=cancel, status=lambda message: progress(10, message))

        self._start_task("위성 검색 중…", task, lambda snapshots: self._search_done(query, snapshots))

    def _search_done(self, query: str, snapshots: list[DataSnapshot]) -> None:
        self._show_matches(snapshots)
        self.source_tabs.setCurrentWidget(self.matches)
        self.store.record_recent("online_query", query, label=f"온라인 검색: {query}")
        self._load_user_lists()

    def import_file(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self, "로컬 위성 자료 열기", "", "위성 자료 (*.json *.tle *.txt);;모든 파일 (*)")
        if not chosen:
            return
        path = Path(chosen)
        self._start_task("로컬 파일 확인 중…", lambda progress, cancel: self.local_service.import_file(path),
                         lambda snapshots: self._import_done(path.name, snapshots))

    def _import_done(self, label: str, snapshots: list[DataSnapshot]) -> None:
        self._show_matches(snapshots)
        self.source_tabs.setCurrentWidget(self.matches)
        if snapshots:
            self.store.record_recent("local_import", label, label=f"로컬 파일: {label}",
                                     file_sha256=str(snapshots[0].source_metadata["file_sha256"]))
            self._load_user_lists()
            self.task_status.setText(f"로컬 파일에서 위성 {len(snapshots)}개를 불러왔습니다.")

    def _load_user_lists(self) -> None:
        self.recent_list.clear()
        for entry in self.store.list_recent(limit=20):
            item = QListWidgetItem(f"{entry.label} · {entry.at_utc}")
            item.setData(Qt.UserRole, entry)
            self.recent_list.addItem(item)
        self.favorite_list.clear()
        for entry in self.store.list_favorites():
            kind = "로컬" if entry.snapshot.source_kind == "local" else "온라인"
            item = QListWidgetItem(f"{entry.label} · NORAD {_id(entry.snapshot)} · {kind}")
            item.setData(Qt.UserRole, entry)
            self.favorite_list.addItem(item)
        self._update_favorite_button()
        self._update_controls()

    def _open_recent(self, item: QListWidgetItem) -> None:
        entry: RecentEntry = item.data(Qt.UserRole)
        if entry.kind == "online_query":
            self.query.setText(entry.query)
            self.search()
            return
        if entry.file_sha256 is None:
            self.task_status.setText("최근 로컬 파일의 저장 정보가 없습니다.")
            return
        def task(progress, cancel):
            if entry.record_index is None:
                return self.local_service.load_import(entry.file_sha256)
            return [self.local_service.load_record(entry.file_sha256, entry.record_index)]

        self._start_task("저장된 로컬 파일 여는 중…", task,
                         lambda snapshots: self._local_recent_done(entry, snapshots))

    def _local_recent_done(self, entry: RecentEntry, snapshots: list[DataSnapshot]) -> None:
        self._show_matches(snapshots)
        self.source_tabs.setCurrentWidget(self.matches)
        self.store.record_recent("local_import", entry.query, label=entry.label,
                                 file_sha256=entry.file_sha256, record_index=entry.record_index)
        self._load_user_lists()
        self.task_status.setText(f"저장된 로컬 위성 {len(snapshots)}개를 열었습니다.")

    def remove_recent(self) -> None:
        item = self.recent_list.currentItem()
        if item is None:
            return
        self.store.remove_recent(item.data(Qt.UserRole).key)
        self._load_user_lists()

    def clear_recent(self) -> None:
        self.store.clear_recent()
        self._load_user_lists()

    def remove_selected_favorite(self) -> None:
        item = self.favorite_list.currentItem()
        if item is None:
            return
        self.store.remove_favorite(item.data(Qt.UserRole).key)
        self._load_user_lists()

    def _open_favorite(self, item: QListWidgetItem) -> None:
        entry: FavoriteEntry = item.data(Qt.UserRole)
        if entry.file_sha256 is not None and entry.record_index is not None:
            self._start_task(
                "저장된 로컬 위성 여는 중…",
                lambda progress, cancel: self.local_service.load_record(entry.file_sha256, entry.record_index),
                lambda snapshot: self._favorite_done(snapshot))
        else:
            def task(progress, cancel):
                progress(5, "즐겨찾기 위성 자료 확인 중…")
                return self.service.get_satellite(
                    _id(entry.snapshot), cancel=cancel, status=lambda message: progress(10, message))

            self._start_task("즐겨찾기 위성 자료 확인 중…", task, self._favorite_done)

    def _favorite_done(self, snapshot: DataSnapshot) -> None:
        self._show_matches([snapshot])
        self.source_tabs.setCurrentWidget(self.matches)
        self.task_status.setText("즐겨찾기 위성 자료를 확인했습니다. 계산 시 자료를 다시 확인합니다."
                                 if snapshot.source_kind == "online" else "저장된 로컬 위성을 선택했습니다.")

    def _favorite_key(self, snapshot: DataSnapshot) -> str | None:
        if snapshot.source_kind == "online":
            return f"online:{_id(snapshot)}"
        if snapshot.source_kind == "local":
            digest = snapshot.source_metadata.get("file_sha256")
            index = snapshot.source_metadata.get("record_index")
            if digest is not None and index is not None:
                return f"local:{digest}:{index}"
        return None

    def _update_favorite_button(self) -> None:
        key = self._favorite_key(self.snapshot) if self.snapshot else None
        present = key is not None and any(
            item.data(Qt.UserRole).key == key for item in
            (self.favorite_list.item(index) for index in range(self.favorite_list.count())))
        self.favorite_button.setText("선택 위성 즐겨찾기 해제" if present else "선택 위성 즐겨찾기 추가")

    def toggle_favorite(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            return
        key = self._favorite_key(snapshot)
        if key is None:
            self.task_status.setText("이 위성은 즐겨찾기에 저장할 수 없습니다.")
            return
        if any(entry.key == key for entry in self.store.list_favorites()):
            self.store.remove_favorite(key)
            self.task_status.setText("즐겨찾기를 해제했습니다.")
        else:
            self.store.add_favorite(snapshot)
            self.task_status.setText("즐겨찾기에 저장했습니다.")
        self._load_user_lists()

    def _show_matches(self, snapshots: list[DataSnapshot]) -> None:
        self.matches.clear()
        self.snapshot = None
        for snapshot in snapshots:
            item = QListWidgetItem(_match_label(snapshot))
            item.setData(Qt.UserRole, snapshot)
            self.matches.addItem(item)
        self.task_status.setText(f"검색 결과 {len(snapshots)}개")
        if snapshots:
            self.matches.setCurrentRow(0)
        else:
            self.source_status.setText("검색 결과가 없습니다.")
        self._update_controls()
        self._update_result_mismatch()
        self._update_favorite_button()

    def _select_satellite(self, current: QListWidgetItem | None, _previous) -> None:
        self.snapshot = current.data(Qt.UserRole) if current is not None else None
        self._show_source_status()
        self._update_controls()
        self._update_result_mismatch()

    def _show_source_status(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            self.source_status.setText("직접 입력값을 확인해 주세요." if self._manual_active()
                                       else "위성을 선택해 주세요.")
            return
        if snapshot.source_kind == "manual":
            gravity = snapshot.source_metadata.get("gravity_model", self.manual_input.gravity_combo.currentData())
            self.source_status.setText(
                f"직접 입력 · GCRS · {_name(snapshot)}"
                f"\n요소시각 UTC: {self._utc_label(self.manual_input.epoch_utc())}"
                f"\n중력: {gravity} · 온라인 위성 요소 사용 안 함")
            return
        age = "오래된 캐시" if snapshot.stale else "확인됨"
        self.source_status.setText(
            f"{'로컬 파일' if snapshot.source_kind == 'local' else '온라인 GP'} · {age}"
            f" · 요소시각 UTC: {snapshot.payload.get('EPOCH', '알 수 없음')}"
            f"\n확인 UTC: {snapshot.checked_at}\n수신 UTC: {snapshot.fetched_at}"
            f"\n출처: {snapshot.source_url}"
            + (f"\n주의: {snapshot.warning}" if snapshot.warning else "")
        )

    @staticmethod
    def _utc_label(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    def _show_result_summary(self) -> None:
        result = self.result
        if result is None:
            self.result_summary.setText("계산 결과가 없습니다.")
            return
        satellite = result.satellite
        request = result.request
        source_kind = {"online": "온라인", "local": "로컬 파일", "manual": "직접 입력",
                       "file": "로컬 파일", "local_file": "로컬 파일"}.get(
            satellite.source_kind, satellite.source_kind)
        identity = f" · NORAD {_id(satellite)}" if satellite.source_kind != "manual" else ""
        summary = (f"계산 결과: {_name(satellite)}{identity} · "
                   f"{source_kind}/{satellite.source_format}\n"
                   f"{self._utc_label(request.start_utc)} ~ {self._utc_label(request.end_utc)}"
                   f" · {request.step_seconds}초 간격\n출처: {satellite.source_url}")
        self.result_summary.setText(summary)
        self.result_summary.setToolTip(summary)

    def _update_result_mismatch(self) -> None:
        result = self.result
        if result is None:
            self.recompute_notice.setText("")
            return
        reasons = []
        current = self.snapshot
        used = result.satellite
        if self._manual_active() != (used.source_kind == "manual"):
            reasons.append("자료 입력 방식")
        elif current is None:
            reasons.append("현재 입력값")
        elif used.source_kind == "manual":
            if current.sha256 != used.sha256:
                reasons.append("직접 입력 궤도/힘 모델")
        elif _id(current) != _id(used):
            reasons.append("선택 위성")
        elif (current.sha256 != used.sha256 or current.source_url != used.source_url
              or current.source_kind != used.source_kind or current.source_format != used.source_format):
            reasons.append("위성 자료")
        request = result.request
        if (self._date_utc(self.start_edit) != request.start_utc
                or self._date_utc(self.end_edit) != request.end_utc
                or self.step_edit.value() != request.step_seconds):
            reasons.append("UTC 계산 구간/간격")
        if self.current_earth_data is not None:
            used_earth = result.provenance.get("earth_data", {})
            if any(self.current_earth_data.provenance.get(key, {}).get("sha256")
                   != used_earth.get(key, {}).get("sha256") for key in ("iers", "leap_seconds")):
                reasons.append("IERS/윤초 자료")
        if reasons:
            self.recompute_notice.setText("현재 " + ", ".join(reasons)
                                          + "가 표시된 계산 결과와 다릅니다. 이전 결과는 계속 보거나 CSV로 저장할 수 있습니다. "
                                            "새 조건을 적용하려면 다시 계산하세요.")
        else:
            self.recompute_notice.setText("")

    @staticmethod
    def _snapshot_status(label: str, snapshot: DataSnapshot | None) -> str:
        if snapshot is None:
            return f"{label}: 없음"
        kind = {"local": "로컬 파일", "manual": "직접 입력"}.get(snapshot.source_kind, "온라인 GP")
        identity = f" · NORAD {_id(snapshot)}" if snapshot.source_kind != "manual" else ""
        return (f"{label}: {_name(snapshot)}{identity}\n"
                f"  자료 형식: {kind} / {snapshot.source_format}\n"
                f"  요소시각 UTC: {snapshot.payload.get('EPOCH', '알 수 없음')}\n"
                f"  수신 UTC: {snapshot.fetched_at or '알 수 없음'}\n"
                f"  마지막 확인 UTC: {snapshot.checked_at or '알 수 없음'}\n"
                f"  캐시 상태: {'오래됨' if snapshot.stale else '유효'}\n"
                f"  출처: {snapshot.source_url}"
                + (f"\n  주의: {snapshot.warning}" if snapshot.warning else ""))

    @staticmethod
    def _earth_status(label: str, provenance: dict) -> str:
        names = (("iers", "IERS 지구 회전"), ("leap_seconds", "윤초"))
        lines = [label]
        for key, title in names:
            info = provenance.get(key, {})
            if not info:
                lines.append(f"  {title}: 없음")
                continue
            kind = "동봉 자료" if info.get("kind") == "bundled" else "다운로드 자료"
            cache = "오래됨" if info.get("stale") else "유효"
            lines.extend((f"  {title}: {kind} · 캐시 {cache}",
                          f"    수신 UTC: {info.get('fetched_at') or '동봉 자료/알 수 없음'}",
                          f"    마지막 확인 UTC: {info.get('checked_at') or '동봉 자료/알 수 없음'}",
                          f"    출처: {info.get('source_url') or '알 수 없음'}"))
        return "\n".join(lines)

    def show_data_status(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("자료 상태")
        dialog.resize(680, 480)
        layout = QVBoxLayout(dialog)
        details = QPlainTextEdit()
        details.setReadOnly(True)
        current_earth = self.current_earth_data.provenance if self.current_earth_data else {}
        result_earth = self.result.provenance.get("earth_data", {}) if self.result else {}
        details.setPlainText("\n\n".join((
            self._snapshot_status("현재 선택 위성 자료", self.snapshot),
            self._earth_status("현재 지구 참조 자료", current_earth),
            self._snapshot_status("표시된 계산 결과의 위성 자료", self.result.satellite if self.result else None),
            self._earth_status("표시된 계산 결과의 지구 참조 자료", result_earth),
        )) + (f"\n\n현재 참조 자료 주의: {self.current_earth_data.warning}"
              if self.current_earth_data and self.current_earth_data.warning else ""))
        layout.addWidget(details)
        close_button = QPushButton("닫기")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)
        self.data_status_dialog = dialog
        dialog.show()

    def refresh_data(self) -> None:
        snapshot = self.snapshot
        if snapshot is None:
            self.task_status.setText("업데이트할 위성을 선택해 주세요.")
            return
        def task(progress, cancel):
            if snapshot.source_kind in ("local", "manual"):
                fresh = snapshot
                progress(5, "위성 입력은 그대로 두고 지구 참조 자료를 확인합니다…")
            else:
                progress(5, "위성 자료 확인 중…")
                fresh = self.service.resolve_satellite(
                    snapshot, force=True, cancel=cancel, status=lambda message: progress(10, message))
            progress(50, "지구 회전 자료 확인 중…")
            earth = self.service.get_earth_data(
                force=True, cancel=cancel, status=lambda message: progress(60, message))
            return fresh, earth

        self._start_task("자료 업데이트 중…", task, self._refresh_done)

    def _refresh_done(self, value) -> None:
        snapshot, earth = value
        self.snapshot = snapshot
        self.current_earth_data = earth
        current = self.matches.currentItem()
        if current is not None and snapshot.source_kind != "manual":
            current.setData(Qt.UserRole, snapshot)
            current.setText(_match_label(snapshot))
        self._show_source_status()
        provider_wait = "next GP check" in snapshot.warning
        self.task_status.setText(("직접 입력 유지 · 지구 참조 자료 확인 완료" if snapshot.source_kind == "manual"
                                  else "로컬 위성 자료 유지 · 지구 참조 자료 확인 완료" if snapshot.source_kind == "local"
                                  else "제공자 갱신 대기 중" if provider_wait else "자료 업데이트 완료")
                                 + (f" · {snapshot.warning}" if snapshot.warning else "")
                                 + (f" · {earth.warning}" if earth.warning else ""))
        self._update_result_mismatch()

    def _date_utc(self, edit: QDateTimeEdit) -> datetime:
        return edit.dateTime().toPython().replace(tzinfo=timezone.utc)

    def calculate(self) -> None:
        snapshot = self.snapshot
        if snapshot is None and not self._manual_active():
            self.task_status.setText("위성을 선택해 주세요.")
            return
        manual = None
        if self._manual_active():
            from orbit_wizard_blue.manual import manual_snapshot, validate_manual_input

            try:
                manual = self.manual_input.build_input()
                validate_manual_input(manual)
                snapshot = manual_snapshot(manual)
            except (ValidationError, ValueError, TypeError) as exc:
                QMessageBox.warning(self, "직접 입력 오류", str(exc))
                return
        request = OrbitRequest(self._date_utc(self.start_edit), self._date_utc(self.end_edit), self.step_edit.value())
        if request.end_utc <= request.start_utc:
            QMessageBox.warning(self, "입력 오류", "종료 시각은 시작 시각보다 늦어야 합니다.")
            return

        def task(progress, cancel):
            from orbit_wizard_blue.orbit import compute_ephemeris

            if manual is not None:
                from orbit_wizard_blue.numerical import compute_manual_ephemeris

                progress(1, "직접 입력 궤도 계산 준비 중…")
                try:
                    earth = self.service.get_earth_data(
                        cancel=cancel, status=lambda message: progress(2, message))
                except CancelledError:
                    raise
                except Exception:
                    earth = None
                    progress(2, "지구 참조 자료 없음 · GCRS 계산을 계속합니다…")
                return compute_manual_ephemeris(
                    manual, request, earth, progress=progress, cancel=cancel), earth
            if snapshot.source_kind == "local":
                current_snapshot = snapshot
                progress(1, "로컬 위성 자료 사용 중…")
            else:
                progress(1, "선택 위성 자료 확인 중…")
                current_snapshot = self.service.resolve_satellite(
                    snapshot, cancel=cancel, status=lambda message: progress(1, message))
            progress(2, "지구 회전 자료 확인 중…")
            earth = self.service.get_earth_data(cancel=cancel, status=lambda message: progress(2, message))
            return compute_ephemeris(current_snapshot, request, earth, progress=progress, cancel=cancel), earth

        self._start_task("직접 입력 궤도 계산 중…" if manual is not None else "궤도 계산 중…",
                         task, self._calculation_done)

    def _calculation_done(self, value: OrbitResult | tuple[OrbitResult, EarthData]) -> None:
        if isinstance(value, tuple):
            result, self.current_earth_data = value
        else:
            result = value
        self.result = result
        self.snapshot = result.satellite
        current = self.matches.currentItem()
        if current is not None and result.satellite.source_kind != "manual":
            current.setData(Qt.UserRole, self.snapshot)
            current.setText(_match_label(self.snapshot))
        self._show_source_status()
        self._show_result_summary()
        self._sample_seconds = [(datetime.fromisoformat(t.replace("Z", "+00:00"))
                                 - datetime.fromisoformat(result.times_utc[0].replace("Z", "+00:00"))).total_seconds()
                                for t in result.times_utc]
        for model in self.models:
            model.set_result(result)
        itrs_available = result.itrs_position_km is not None
        self.frame_combo.model().item(1).setEnabled(itrs_available)
        if not itrs_available and self.frame_combo.currentData() == "ITRS":
            self.frame_combo.setCurrentIndex(0)
        self.orbit_view.set_result(result)
        self.ground_track_view.set_result(result)
        self.slider.setRange(0, max(0, len(result.times_utc) - 1))
        self.set_sample_index(0)
        self._update_result_mismatch()
        self.task_status.setText(f"계산 완료 · {len(result.times_utc):,}개 샘플"
                                 + (f" · 주의: {'; '.join(result.warnings)}" if result.warnings else ""))
        self.progress.setValue(100)
        self._update_controls()

    def export_result(self) -> None:
        result = self.result
        if result is None:
            return
        proposed = (f"orbit-{_id(result.satellite)}.csv" if result.satellite.source_kind != "manual"
                    else "orbit-manual.csv")
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
        self.ground_track_view.set_index(index)
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
        manual = self._manual_active()
        self.source_tabs.setEnabled(not busy)
        self.search_button.setEnabled(not busy)
        self.import_button.setEnabled(not busy)
        self.matches.setEnabled(not busy)
        self.recent_list.setEnabled(not busy)
        self.favorite_list.setEnabled(not busy)
        self.remove_recent_button.setEnabled(not busy and self.recent_list.currentItem() is not None)
        self.clear_recent_button.setEnabled(not busy and self.recent_list.count() > 0)
        self.remove_favorite_button.setEnabled(not busy and self.favorite_list.currentItem() is not None)
        self.query.setEnabled(not busy)
        self.manual_input.setEnabled(not busy)
        self.refresh_button.setEnabled(not busy and self.snapshot is not None)
        self.favorite_button.setEnabled(not busy and not manual and self.snapshot is not None)
        self.calculate_button.setEnabled(not busy and (self.snapshot is not None or manual))
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
