from __future__ import annotations

from pathlib import Path


def resolve_default_fixture_path(start_dir: Path | None = None) -> Path | None:
    current = (start_dir or Path.cwd()).resolve()
    roots = [current, *current.parents]
    for root in roots:
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            fixture = root / "tests" / "fixtures" / "awzi_haarlem_waarderpolder_demo.rcm.json"
            if fixture.exists():
                return fixture
            return None
    return None
