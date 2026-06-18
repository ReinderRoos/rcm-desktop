from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

files = [
    ROOT / "tests/test_desktop_results_workspace_window.py",
    ROOT / "tests/test_desktop_meekoppel_workspace.py",
    ROOT / "tests/test_lcc_whatif_workspace_visibility.py",
    ROOT / "tests/test_workspace_modus_ui_ab.py",
    ROOT / "tests/test_slice74_window.py",
    ROOT / "scripts/capture_gebruikershandleiding_screenshots.py",
]
replacements = [
    ('window.modus_buttons["fm_detail"].click()', 'switch_workspace_modus(window, "fm_detail", app)'),
    ('window.modus_buttons["lcc"].click()', 'switch_workspace_modus(window, "lcc", app)'),
    ('window.modus_buttons["bijdragen"].click()', 'switch_workspace_modus(window, "bijdragen", app)'),
    ('window.modus_buttons[MODE_FM_DETAIL].click()', 'switch_workspace_modus(window, MODE_FM_DETAIL, app)'),
    ('window.modus_buttons[MODE_LCC].click()', 'switch_workspace_modus(window, MODE_LCC, app)'),
    ('window.modus_buttons[MODE_BIJDRAGEN].click()', 'switch_workspace_modus(window, MODE_BIJDRAGEN, app)'),
]
for path in files:
    text = path.read_text(encoding="utf-8")
    orig = text
    for old, new in replacements:
        text = text.replace(old, new)
    if text != orig and "from tests.workspace_test_helpers import switch_workspace_modus" not in text:
        lines = text.splitlines(True)
        idx = 0
        for i, line in enumerate(lines):
            if line.startswith("from ") or line.startswith("import "):
                idx = i + 1
        lines.insert(idx, "from tests.workspace_test_helpers import switch_workspace_modus\n")
        text = "".join(lines)
    if text != orig:
        path.write_text(text, encoding="utf-8")
        print("updated", path.relative_to(ROOT))
