#!/usr/bin/env python3
"""Deterministic compatibility upgrades for legacy local data files."""

from __future__ import annotations

import json
import shutil
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.config import (
    BASE_DIR,
    HISTORY_FILE,
    ORDERS_FILE,
    PRIVATE_DIR,
    PUBLIC_DIR,
    SETTINGS_FILE,
    TOKEN_FILE,
    _set_private_permissions,
)


def _legacy_private_files() -> Dict[str, Path]:
    return {
        "tesla_tokens.json": TOKEN_FILE,
        "tesla_orders.json": ORDERS_FILE,
        "tesla_order_history.json": HISTORY_FILE,
        "settings.json": SETTINGS_FILE,
    }


def _legacy_public_files() -> Dict[str, Path]:
    return {
        "tesla_locations.json": PUBLIC_DIR / "tesla_locations.json",
    }


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_json(path: Path, payload: Any, private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)
    if private:
        _set_private_permissions(path)


def _safe_move_with_backup(src: Path, dst: Path, backup_dir: Path) -> bool:
    try:
        src_stat = src.stat()
    except FileNotFoundError:
        return False

    if not dst:
        src.unlink(missing_ok=True)
        return True

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst_stat = dst.stat()
        backup_dir.mkdir(parents=True, exist_ok=True)
        if src_stat.st_mtime > dst_stat.st_mtime:
            shutil.move(str(dst), str(backup_dir / (dst.name + ".old")))
            shutil.move(str(src), str(dst))
            return True
        shutil.move(str(src), str(backup_dir / (src.name + ".old")))
        return True

    shutil.move(str(src), str(dst))
    return True


def migrate_legacy_layout() -> List[str]:
    backup_dir = PRIVATE_DIR / "backup"
    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    PUBLIC_DIR.mkdir(parents=True, exist_ok=True)

    changed: List[str] = []
    for name, destination in {
        **_legacy_private_files(),
        **_legacy_public_files(),
    }.items():
        source = BASE_DIR / name
        if source.exists() and _safe_move_with_backup(source, destination, backup_dir):
            changed.append(f"moved {name} -> {destination.relative_to(BASE_DIR)}")
            if destination.is_file() and destination.parent == PRIVATE_DIR:
                _set_private_permissions(destination)
    return changed


def _extract_reference(entry: Any) -> Optional[str]:
    if not isinstance(entry, dict):
        return None
    order_payload = entry.get("order")
    if isinstance(order_payload, dict):
        reference = order_payload.get("referenceNumber")
        if reference:
            return str(reference)
    reference = entry.get("referenceNumber")
    if reference:
        return str(reference)
    return None


def _build_index_map() -> Dict[str, str]:
    if not ORDERS_FILE.exists():
        return {}
    try:
        orders_data = _read_json(ORDERS_FILE)
    except Exception:
        return {}

    mapping: Dict[str, str] = {}
    if isinstance(orders_data, list):
        for index, entry in enumerate(orders_data):
            reference = _extract_reference(entry)
            if reference:
                mapping[str(index)] = reference
    elif isinstance(orders_data, dict):
        for key, entry in orders_data.items():
            reference = _extract_reference(entry)
            if reference:
                mapping[str(key)] = reference
    return mapping


def _resolve_reference_and_key(
    change: Dict[str, Any], index_map: Dict[str, str]
) -> Tuple[Optional[str], str]:
    raw_key = change.get("key")
    key_text = raw_key if isinstance(raw_key, str) else ""

    if "." in key_text:
        prefix, remainder = key_text.split(".", 1)
    else:
        prefix, remainder = key_text, ""

    reference = change.get("order_reference")
    if reference is None and prefix:
        if prefix in index_map:
            reference = index_map[prefix]
        elif prefix.upper().startswith("RN"):
            reference = prefix
        elif prefix.isdigit():
            reference = prefix

    if reference is None:
        return None, key_text
    if remainder:
        return str(reference), remainder
    return str(reference), key_text


def migrate_legacy_history() -> bool:
    if not HISTORY_FILE.exists():
        return False

    try:
        history_data = _read_json(HISTORY_FILE)
    except Exception:
        return False

    if isinstance(history_data, dict):
        return False
    if not isinstance(history_data, list):
        return False

    index_map = _build_index_map()
    migrated: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for entry in history_data:
        if not isinstance(entry, dict):
            continue
        reference, cleaned_key = _resolve_reference_and_key(entry, index_map)
        if reference is None:
            continue
        updated_entry = dict(entry)
        updated_entry["order_reference"] = reference
        updated_entry["key"] = cleaned_key
        migrated[reference].append(updated_entry)

    if not migrated:
        return False

    _write_json(HISTORY_FILE, dict(sorted(migrated.items())), private=True)
    return True


def run_legacy_compatibility_migration() -> List[str]:
    changes = migrate_legacy_layout()
    if migrate_legacy_history():
        changes.append("converted tesla_order_history.json to reference-based format")
    return changes
