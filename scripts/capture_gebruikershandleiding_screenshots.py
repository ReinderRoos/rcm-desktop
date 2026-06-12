#!/usr/bin/env python3
"""Genereer UI-screenshots voor docs/gebruiker/HANDLEIDING.md (PySide6).

Gebruik:
  python scripts/capture_gebruikershandleiding_screenshots.py

Vereist: pip install -e .[dev] en een werkende Qt-platform plugin (Windows GUI of offscreen).
"""

from __future__ import annotations

import sys
from pathlib import Path
from tests.workspace_test_helpers import switch_workspace_modus

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "tests" / "fixtures" / "sample_project.rcm.json"
OUT_DIR = REPO_ROOT / "docs" / "gebruiker" / "screenshots"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _ensure_app():
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


def _grab(widget, path: Path) -> None:
    from PySide6.QtCore import QSize
    from PySide6.QtGui import QPixmap

    path.parent.mkdir(parents=True, exist_ok=True)
    widget.adjustSize()
    pixmap: QPixmap = widget.grab()
    if pixmap.isNull():
        raise RuntimeError(f"Grab failed for {path.name}")
    # Consistente breedte voor handleiding (max 1400px)
    if pixmap.width() > 1400:
        from PySide6.QtCore import Qt

        pixmap = pixmap.scaledToWidth(1400, Qt.TransformationMode.SmoothTransformation)
    if not pixmap.save(str(path), "PNG"):
        raise RuntimeError(f"Save failed: {path}")


def _setup_window():
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QMessageBox

    from rcm_core.persistence import load_project
    from rcm_desktop.adapter.loaded_project import LoadedProject
    from rcm_desktop.adapter.project_session import ProjectSession
    from rcm_desktop.adapter.results_workspace_state import MODE_BIJDRAGEN, MODE_FM_DETAIL, MODE_LCC
    from rcm_desktop.views.report_generation_dialog import ReportGenerationDialog
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    from rcm_desktop.adapter.presentation_cache_service import build_project_total_presentation
    from rcm_desktop.adapter.run_service import run as run_single

    def _inject_run(win: ResultsWorkspaceWindow, proj) -> object:
        run_result = run_single(proj, FIXTURE)
        presentation = (
            build_project_total_presentation(proj, run_result)
            if run_result.status == "done"
            else None
        )
        win._on_run_result_ready(run_result, presentation)
        return run_result

    # Geen blokkerende message boxes tijdens capture
    def _msgbox_ok(*_a, **_k):
        return QMessageBox.StandardButton.Ok

    QMessageBox.critical = _msgbox_ok  # type: ignore[method-assign]
    QMessageBox.information = _msgbox_ok  # type: ignore[method-assign]
    QMessageBox.warning = _msgbox_ok  # type: ignore[method-assign]

    project = load_project(FIXTURE)
    window = ResultsWorkspaceWindow()
    window.resize(1440, 900)
    window.show()
    window.path_input.setText(str(FIXTURE))
    window._state.set_last_project(project)
    run = _inject_run(window, project)
    loaded = LoadedProject.from_core(project)
    window._state._last_project = project
    window._state._loaded_project = loaded
    window._state._last_run = run
    window._state._project_session = ProjectSession.from_parts(
        loaded,
        path=FIXTURE,
        run=run,
    )
    app = _ensure_app()
    app.processEvents()
    return app, window, project, run, ReportGenerationDialog, MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL


def main() -> int:
    try:
        import PySide6  # noqa: F401
    except ImportError:
        print("PySide6 ontbreekt. Voer uit: pip install -e .[dev]")
        return 1

    app, window, project, run, ReportGenerationDialog, MODE_BIJDRAGEN, MODE_LCC, MODE_FM_DETAIL = _setup_window()

    # 01 — volledige werkruimte na run
    window.workspace_state.set_modus(MODE_BIJDRAGEN)
    app.processEvents()
    _grab(window, OUT_DIR / "01-werkruimte-overzicht.png")

    # 02 — toolbar met pad (zelfde venster, focus op bovenkant — volledige grab volstaat)
    _grab(window, OUT_DIR / "02-toolbar-project-pad.png")

    # 03 — PBS-scope
    pbs_ids = list(project.pbs_items)
    if pbs_ids:
        window.set_pbs_scope(pbs_ids[-1])
        app.processEvents()
    _grab(window, OUT_DIR / "03-pbs-scope-geselecteerd.png")
    window.show_whole_project_button.click()
    app.processEvents()

    # 04 — Top 10
    switch_workspace_modus(window, MODE_BIJDRAGEN, app)
    app.processEvents()
    _grab(window, OUT_DIR / "04-modus-top10.png")

    # 05 — Tijdsplot + planning-paneel uitgeklapt
    switch_workspace_modus(window, MODE_LCC, app)
    window.workspace_state.set_lcc_whatif_collapsed_in_lcc(False)
    app.processEvents()
    _grab(window, OUT_DIR / "05-modus-tijdsplot-planning.png")

    # 06 — FM-detail + inspector
    switch_workspace_modus(window, MODE_FM_DETAIL, app)
    app.processEvents()
    model = window.fm_table_view.model()
    if model is not None and model.rowCount() > 0:
        window.fm_table_view.selectRow(0)
        app.processEvents()
    _grab(window, OUT_DIR / "06-modus-fm-detail-inspector.png")

    # 07 — rapportdialoog
    from rcm_desktop.adapter.project_path_resolution_service import resolve_project_file_path

    resolved = resolve_project_file_path(
        session_path=FIXTURE,
        path_text=str(FIXTURE),
    )
    default_path = resolved.default_report_output_path(project)
    assert default_path is not None
    dialog = ReportGenerationDialog(
        window,
        project=project,
        project_path=FIXTURE,
        last_run=run,
        compare_slots=window._compare_slots,
        live_overlay=window.workspace_state.snapshot().planning_overlay,
        default_output_path=default_path,
        scope_id=window.workspace_state.snapshot().scope_id,
    )
    dialog.resize(520, 480)
    dialog.show()
    app.processEvents()
    _grab(dialog, OUT_DIR / "07-rapport-dialoog.png")
    dialog.close()

    # 08 — rapportknop disabled (venster zonder run)
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    empty = ResultsWorkspaceWindow()
    empty.resize(1440, 900)
    empty.show()
    app.processEvents()
    _grab(empty, OUT_DIR / "08-werkruimte-zonder-run.png")
    empty.close()

    print(f"Screenshots geschreven naar {OUT_DIR}")
    for p in sorted(OUT_DIR.glob("*.png")):
        print(f"  {p.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
