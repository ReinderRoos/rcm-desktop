"""Buffer-brede hervalidatie van invoerbevindingen (slice 88)."""

from __future__ import annotations

from rcm_desktop.adapter.editing_session import EditingSession
from rcm_desktop.adapter.input_grid_findings import inject_input_grid_findings


def revalidate_input_buffer(session: EditingSession) -> None:
    if not session.is_loaded or session.base_project is None:
        return
    session.validate()
    inject_input_grid_findings(session.session, base_project=session.base_project)
