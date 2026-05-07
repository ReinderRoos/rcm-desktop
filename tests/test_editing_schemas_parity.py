"""Parity: ENTITY_SCHEMAS field names must exist on the linked dataclass."""
from __future__ import annotations

import sys
from dataclasses import fields, is_dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from rcm_core.editing.schemas import ENTITY_SCHEMAS


def test_entity_schemas_keys_exist_on_model_class() -> None:
    for entity_name, schema in ENTITY_SCHEMAS.items():
        cls = schema["class"]
        assert is_dataclass(cls), f"{entity_name}: schema class must be a @dataclass"
        names = {f.name for f in fields(cls)}

        assert schema["key_field"] in names, (
            f"{entity_name}: key_field {schema['key_field']!r} missing on {cls.__name__}"
        )
        for field in schema["required_fields"]:
            assert field in names, (
                f"{entity_name}: required_fields contains {field!r} but {cls.__name__} has no such field"
            )
        for field in schema["field_types"]:
            assert field in names, (
                f"{entity_name}: field_types has {field!r} but {cls.__name__} has no such field"
            )
        for field in schema["fk_rules"]:
            assert field in names, (
                f"{entity_name}: fk_rules key {field!r} but {cls.__name__} has no such field"
            )
