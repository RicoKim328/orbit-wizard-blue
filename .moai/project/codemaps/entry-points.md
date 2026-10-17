# Codemap: Entry Points

## Application

| Entry | Target |
|---|---|
| `python -m orbit_wizard_blue` | `src/orbit_wizard_blue/__main__.py` `main()` |
| Console script `orbit-wizard-blue` | `orbit_wizard_blue.__main__:main` (`pyproject.toml`) |
| Frozen exe `dist/orbit-wizard-blue/orbit-wizard-blue.exe` | same `__main__.py` (PyInstaller spec) |

## CLI flags (`__main__.py:122-126`)

| Flag | Behavior |
|---|---|
| (none) | configure logging, launch `MainWindow` |
| `--smoke-test` | distribution check that opens no window but still initializes a `QApplication` (`__main__.py:69`), so a display-less Linux host needs `QT_QPA_PLATFORM=offscreen`; (`smoke_test()`; verifies export metadata `schema_version` 3) |
| `--smoke-output FILE` | write smoke result JSON |
| `--gui-check` | real GUI and synchronization check (`gui_validation.run_gui_check`) |
| `--gui-check-output-dir DIR` | output folder for GUI check report (`gui-check-report.json`) |

## Developer tools (`tools/`, not packaged)

| Script | Lines | Purpose |
|---|---:|---|
| `capture_gui.py` | 176 | capture GUI screenshots from an offline validation example (`--output-dir assets/screenshots`) |
| `check_live_data.py` | 71 | one-shot live source and 24-hour calculation check; required `--cache-dir` |
| `validate_orbit.py` | 129 | reproducible offline orbit fixture and 100,000-sample validation; `--orbit meo\|geo`, `--count` |
