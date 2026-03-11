"""Utilities for retrieving Tesla option codes from local JSON catalogs."""

from __future__ import annotations

import json
from glob import glob
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import PUBLIC_DIR

_OPTION_CODES: Optional[Dict[str, Dict[str, Any]]] = None


def _normalize_entry(value: Any) -> Optional[Dict[str, Any]]:
    """Return a uniform option-code payload with at least label/category."""
    if isinstance(value, dict):
        label = value.get("label") or value.get("label_en") or value.get("label_en_us")
        label_short = value.get("label_short") or value.get("label_en_short")
        if label is None and "raw" in value:
            raw = value.get("raw")
            if isinstance(raw, dict):
                label = raw.get("label") or raw.get("label_en")
                if label_short is None:
                    label_short = raw.get("label_en_short")
        category = value.get("category")
        raw_payload = value.get("raw")
        if raw_payload is None:
            # Preserve original payload for future use if we have access to it
            raw_payload = {
                k: v
                for k, v in value.items()
                if k
                not in {
                    "label",
                    "label_en",
                    "label_en_us",
                    "label_short",
                    "label_en_short",
                    "category",
                    "raw",
                }
            } or None
        if label is None:
            return None
        entry = {
            "label": str(label),
            "category": (
                str(category).strip().lower() if isinstance(category, str) else None
            ),
        }
        if isinstance(label_short, str) and label_short.strip():
            entry["label_short"] = label_short.strip()
        if raw_payload:
            entry["raw"] = raw_payload
        return entry

    if value is None:
        return None

    return {
        "label": str(value),
        "category": None,
    }


def _load_local_overrides() -> Dict[str, Dict[str, Any]]:
    folder = PUBLIC_DIR / "option-codes"
    option_codes: Dict[str, Dict[str, Any]] = {}
    if not folder.exists() or not folder.is_dir():
        return option_codes

    for path in sorted(glob(str(folder / "*.json"))):
        try:
            with Path(path).open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            for code, value in payload.items():
                key = str(code).strip().upper()
                entry = _normalize_entry(value)
                if entry:
                    option_codes[key] = entry
    return option_codes


def _apply_local_overrides(
    option_codes: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    overrides = _load_local_overrides()
    if not overrides:
        return option_codes
    merged = option_codes.copy()
    merged.update(overrides)
    return merged


def get_option_codes(force_refresh: bool = False) -> Dict[str, Dict[str, Any]]:
    """Return a dictionary mapping option codes to local metadata."""
    global _OPTION_CODES

    if not force_refresh and _OPTION_CODES is not None:
        return _OPTION_CODES

    _OPTION_CODES = _load_local_overrides()
    return _OPTION_CODES


def get_option_label(code: str) -> Optional[str]:
    """Return the label for *code* if it exists."""
    if not isinstance(code, str):
        return None
    entry = get_option_codes().get(code.strip().upper())
    if not entry:
        return None
    return entry.get("label")


def get_option_entry(code: str) -> Optional[Dict[str, Any]]:
    """Return the normalized option-code entry if available."""
    if not isinstance(code, str):
        return None
    entry = get_option_codes().get(code.strip().upper())
    if entry is None:
        return None
    # Return a shallow copy to prevent accidental mutations of the cache
    return dict(entry)


def get_option_category(code: str) -> Optional[str]:
    """Return the normalized category for *code*."""
    entry = get_option_entry(code)
    if not entry:
        return None
    return entry.get("category")
