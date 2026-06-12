from __future__ import annotations

from pathlib import Path


_DEFAULT_FIXTURE_NAMES = (
    "RCMCostdata export_Gaarkeuken_CM.rcm.rcm.json",
    "awzi_haarlem_waarderpolder_demo.rcm.json",
)


def resolve_default_fixture_path(start_dir: Path | None = None) -> Path | None:
    current = (start_dir or Path.cwd()).resolve()
    roots = [current, *current.parents]
    for root in roots:
        pyproject = root / "pyproject.toml"
        if pyproject.exists():
            for name in _DEFAULT_FIXTURE_NAMES:
                fixture = root / "tests" / "fixtures" / name
                if fixture.exists():
                    return fixture
            return None
    return None
