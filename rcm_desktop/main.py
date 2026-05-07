"""Entry point voor de RCM2 desktop-app.

Tracer-bullet stub: laad fixture, toon één faalwijzentabel + run-knop + Top-X-tabel.
Implementatie volgt issues onder `.scratch/rcm-desktop-tracer-bullet/`.
"""
from __future__ import annotations

import sys


def main() -> int:
    try:
        from PySide6.QtWidgets import QApplication, QLabel, QMainWindow
    except ImportError:
        print(
            "PySide6 is niet geinstalleerd. Voer eerst uit:\n"
            "  pip install -e .[dev]\n"
            "vanuit de rcm-desktop directory."
        )
        return 1

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("RCM2 desktop — tracer-bullet (placeholder)")
    win.setCentralWidget(QLabel("Placeholder. Zie .scratch/rcm-desktop-tracer-bullet/ voor werkpakket."))
    win.resize(640, 360)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
