# Codemap: Modules

Public interfaces (class, function and public-method names verified by grep).

| Module | Public interface | Responsibility |
|---|---|---|
| `models` | `ValidationError`, `CancelledError`, `freeze_json`, `thaw_json`, `DataSnapshot`, `EarthData`, `OrbitRequest`, `OrbitResult` | shared types |
| `validation` | `gp_items(raw, *, allow_empty=False)` | GP JSON validation |
| `tle` | `ParsedTle`, `parse_tle(text)` | TLE parsing to OMM-shaped records |
| `cache_lock` | `thread_lock(...)`, `process_lock(...)` | cancel-aware in-process and cross-process locks |
| `data` | `DataService.search_satellites`, `get_satellite`, `resolve_satellite`, `get_earth_data`; `CACHE_SECONDS=7200`, `TIMEOUT_SECONDS=8`, `GP_URL` | CelesTrak + IERS client with cache |
| `local_data` | `LocalDataService.import_file`, `load_import`, `load_record`; `MAX_FILE_BYTES=20_000_000` | local file import |
| `user_store` | `UserStore.record_recent`, `list_recent`, `remove_recent`, `clear_recent`, `add_favorite`, `list_favorites`, `remove_favorite`, `clear_favorites`; `RecentEntry`, `FavoriteEntry` | SQLite recent/favorites |
| `orbit` | `compute_ephemeris(...)` | SGP4 ephemeris and frame transforms |
| `manual` | `KeplerianElements`, `ConstantAcceleration`, `ManualOrbitInput`, `validate_manual_input`, `manual_snapshot`, `MU`, `J2`, `EARTH_RADIUS_KM` | manual input model |
| `numerical` | `elements_to_state`, `compute_manual_ephemeris(...)` | numerical propagation (`_MAX_INTEGRATION_SPAN_S = 3600.0`) |
| `ground_track` | `ground_track_plot(geodetic_deg_km)` | ground-track arrays |
| `export` | `export_ephemeris(result, path) -> (csv, json)` | CSV + metadata JSON v3 |
| `gl_platform` | `configure_pyopengl()` | OpenGL platform setup |
| `gl_software_win32` | `QtSoftwareWin32Platform` | Windows software OpenGL |
| `gui_validation` | `run_gui_check(output_dir) -> int` | frozen GUI check |
| `gui.window` | `MainWindow` | main window |
| `gui.workers` | `TaskWorker` (signals `progress`, `succeeded`, `failed`, `cancelled`; `request_cancel`) | background tasks |
| `gui.manual_input` | `ManualInputWidget` | manual form |
| `gui.orbit_view` | `OrbitView` | 3D view |
| `gui.ground_track_view` | `GroundTrackView`, `coastline_points` | ground track view |
| `gui.tables` | `OrbitTableModel`, `configure_table_columns` | ephemeris table |
