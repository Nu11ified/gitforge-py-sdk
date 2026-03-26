from __future__ import annotations

import re
from dataclasses import fields
from typing import Any, Type, TypeVar

T = TypeVar("T")

_CAMEL_RE = re.compile(r"(?<!^)(?=[A-Z])")


def _to_snake(d: dict[str, Any]) -> dict[str, Any]:
    """Convert camelCase dict keys to snake_case for dataclass construction."""
    return {_CAMEL_RE.sub("_", k).lower(): v for k, v in d.items()}


def _from_dict(cls: Type[T], data: dict[str, Any]) -> T:
    """Construct a dataclass from a camelCase API dict, ignoring unknown keys."""
    snake = _to_snake(data)
    valid_keys = {f.name for f in fields(cls)}
    return cls(**{k: v for k, v in snake.items() if k in valid_keys})
