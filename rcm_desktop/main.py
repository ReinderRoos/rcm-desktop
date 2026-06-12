"""Entry point voor de RCM2 desktop-app (resultatenwerkruimte)."""
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

    from rcm_desktop.views.results_workspace_window import ResultsWorkspaceWindow

    app = QApplication(sys.argv)
    window = ResultsWorkspaceWindow()
    window.setWindowTitle("RCM2 — resultatenwerkruimte")
    app.aboutToQuit.connect(window.cancel_background_runners)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
