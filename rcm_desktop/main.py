"""Entry point voor de RCM desktop-app (resultatenwerkruimte)."""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(
            "PySide6 is niet geinstalleerd. Voer eerst uit:\n"
            "  pip install -e .[dev]\n"
            "vanuit de rcm-desktop directory."
        )
        return 1

    try:
        import openpyxl  # noqa: F401
    except ImportError:
        print(
            "openpyxl is niet geinstalleerd (nodig voor RCM-Cost import). Voer uit:\n"
            "  pip install -e .\n"
            "of: pip install openpyxl>=3.1\n"
            "vanuit de rcm-desktop directory."
        )
        return 1

    from rcm_desktop.desktop_tooltip import apply_desktop_tooltip_polish
    from rcm_desktop.theme.rcm2_theme import apply_rcm2_theme
    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = QApplication(sys.argv)
    apply_rcm2_theme(app)
    apply_desktop_tooltip_polish(app)
    window = ResultsWorkspaceWindow()
    window.setWindowTitle("RCM — Delta Pi")
    app.aboutToQuit.connect(window.cancel_background_runners)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
