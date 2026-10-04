"""Shared serialization mixin for acquisition platform dataclasses.

Provides generic ``to_dict`` / ``from_dict`` behavior so every result type
can be persisted, exported, and reconstructed without bespoke code per class.

The encoder recursively converts nested dataclasses (e.g. ``Portfolio`` ->
``list[Asset]``) into plain JSON-compatible structures. The decoder uses the
class's resolved type hints to rebuild nested dataclasses from dicts, and
falls back to dataclass defaults for any field absent from the input.
"""
from __future__ import annotations

import dataclasses
import typing
from typing import Any, get_args, get_origin, get_type_hints


def _encode(value: Any) -> Any:
    """Recursively convert a value into a JSON-compatible structure."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: _encode(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    if isinstance(value, list):
        return [_encode(v) for v in value]
    if isinstance(value, tuple):
        return [_encode(v) for v in value]
    if isinstance(value, dict):
        return {k: _encode(v) for k, v in value.items()}
    return value


def _is_dataclass_type(tp: Any) -> bool:
    return isinstance(tp, type) and dataclasses.is_dataclass(tp)


def _decode_value(value: Any, tp: Any) -> Any:
    """Rebuild nested dataclasses using the declared field type."""
    if value is None:
        return None
    origin = get_origin(tp)
    if origin in (list, typing.List):
        args = get_args(tp)
        if args and _is_dataclass_type(args[0]) and isinstance(value, list):
            return [_decode_value(v, args[0]) for v in value]
        return value
    if origin in (dict, typing.Dict):
        return value
    if _is_dataclass_type(tp) and isinstance(value, dict):
        return tp.from_dict(value)
    return value


class SerializableMixin:
    """Mixin adding ``to_dict`` / ``from_dict`` to a dataclass."""

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-compatible dict of this dataclass's fields."""
        return {
            f.name: _encode(getattr(self, f.name))
            for f in dataclasses.fields(self)  # type: ignore[arg-type]
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SerializableMixin":
        """Reconstruct an instance from a dict produced by ``to_dict``.

        Fields absent from ``data`` are left to the dataclass's own defaults.
        """
        hints = get_type_hints(cls)
        kwargs: dict[str, Any] = {}
        for f in dataclasses.fields(cls):  # type: ignore[arg-type]
            if f.name not in data:
                continue
            kwargs[f.name] = _decode_value(data[f.name], hints.get(f.name, Any))
        return cls(**kwargs)
