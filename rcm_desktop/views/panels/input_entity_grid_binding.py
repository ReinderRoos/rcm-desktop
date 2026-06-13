"""Input-zijde entity-grid pagina voor de resultatenwerkruimte (slice 93)."""

from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from rcm_desktop import messages
from rcm_desktop.views.panels.entity_grid_panel import EntityGridPanel


def build_input_entity_grid_page(window: Any) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    layout.setContentsMargins(0, 0, 0, 0)
    toolbar = QHBoxLayout()
    window.new_fm_button = QPushButton(messages.FM_EDITOR_NEW_FM)
    window.new_fm_button.setToolTip(messages.FM_EDITOR_NEW_FM_TOOLTIP)
    window.new_fm_button.setVisible(False)
    toolbar.addWidget(window.new_fm_button)
    toolbar.addStretch(1)
    layout.addLayout(toolbar)
    window._entity_grid_panel = EntityGridPanel()
    window._entity_grid_panel.set_hidden_columns_handler(window._on_entity_grid_columns_changed)
    layout.addWidget(window._entity_grid_panel)
    window.new_fm_button.clicked.connect(window._on_new_fm_clicked)
    return page
