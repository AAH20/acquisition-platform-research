"""Data export and import utilities for the acquisition platform.

Provides JSON, CSV, and YAML serialization helpers plus schema validation.
All functions raise FileNotFoundError for missing input files and
OSError for unwritable output paths.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Any

import yaml  # type: ignore[import-untyped]


def export_to_json(data: Any, path: str) -> None:
    """Export data to a JSON file.

    Args:
        data: Any JSON-serializable Python object.
        path: Destination file path.

    Raises:
        OSError: If the path is not writable.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def import_from_json(path: str) -> Any:
    """Import data from a JSON file.

    Args:
        path: Source file path.

    Returns:
        The deserialized Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def export_to_csv(data: list[dict[str, Any]], path: str) -> None:
    """Export a list of dicts to a CSV file.

    The union of all keys across dicts is used as the header.
    Missing keys in individual rows are written as empty strings.

    Args:
        data: List of dicts with consistent or overlapping keys.
        path: Destination file path.

    Raises:
        OSError: If the path is not writable.
    """
    if not data:
        with open(path, "w", encoding="utf-8", newline="") as f:
            pass
        return

    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in data:
        for key in row:
            if key not in seen:
                fieldnames.append(key)
                seen.add(key)

    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def import_from_csv(path: str) -> list[dict[str, str]]:
    """Import a CSV file as a list of dicts.

    Args:
        path: Source file path.

    Returns:
        List of dicts, one per row.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def export_to_yaml(data: Any, path: str) -> None:
    """Export data to a YAML file.

    Args:
        data: Any YAML-serializable Python object.
        path: Destination file path.

    Raises:
        OSError: If the path is not writable.
    """
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)


def import_from_yaml(path: str) -> Any:
    """Import data from a YAML file.

    Args:
        path: Source file path.

    Returns:
        The deserialized Python object.

    Raises:
        FileNotFoundError: If the file does not exist.
        yaml.YAMLError: If the file contains invalid YAML.
    """
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_schema(data: dict[str, Any], schema: dict[str, type]) -> bool:
    """Validate that a dict conforms to a type schema.

    Every key in schema must exist in data with a value of the
    specified type. Extra keys in data are allowed.

    Args:
        data: The dict to validate.
        schema: Mapping of field name to expected type.

    Returns:
        True if data matches the schema, False otherwise.
    """
    for field_name, expected_type in schema.items():
        if field_name not in data:
            return False
        if not isinstance(data[field_name], expected_type):
            return False
    return True
