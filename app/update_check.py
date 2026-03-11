#!/usr/bin/env python3
# coding: utf-8
"""Check for trusted release updates without sending user data to third parties.

Exit codes:
  0 -> everything up to date
  1 -> newer release available
  2 -> local files missing or update action pending
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import sys
import webbrowser

from app.config import (
    APP_DIR,
    BASE_DIR,
    PUBLIC_DIR,
    TESLA_STORES_FILE,
    VERSION,
    cfg as Config,
)
from app.utils.colors import color_text
from app.utils.connection import request_with_retry
from app.utils.locale import t
from app.utils.params import STATUS_MODE

FILES_TO_CHECK: List[Path] = [
    BASE_DIR / "tesla_order_status.py",
    BASE_DIR / "hotfix.py",
    TESLA_STORES_FILE,
    PUBLIC_DIR / "lang" / "de.json",
    PUBLIC_DIR / "lang" / "en.json",
    PUBLIC_DIR / "lang" / "pl.json",
    PUBLIC_DIR / "lang" / "sv.json",
    APP_DIR / "config.py",
    APP_DIR / "update_check.py",
    APP_DIR / "utils" / "auth.py",
    APP_DIR / "utils" / "colors.py",
    APP_DIR / "utils" / "connection.py",
    APP_DIR / "utils" / "helpers.py",
    APP_DIR / "utils" / "history.py",
    APP_DIR / "utils" / "migration.py",
    APP_DIR / "utils" / "orders.py",
    APP_DIR / "utils" / "params.py",
    APP_DIR / "utils" / "timeline.py",
    APP_DIR / "migrations" / "2025-08-23-history.py",
    APP_DIR / "migrations" / "2025-08-30-datafolders.py",
]

RELEASE_API_URL = (
    "https://api.github.com/repos/enoch85/tesla-order-status/releases/latest"
)
RELEASE_PAGE_URL = "https://github.com/enoch85/tesla-order-status/releases/latest"


def _parse_version(tag: str) -> Optional[Tuple[int, ...]]:
    if not isinstance(tag, str):
        return None
    text = tag.strip()
    if not text:
        return None
    if text[0] in {"v", "V", "p", "P"}:
        text = text[1:]
    parts = text.split(".")
    parsed: List[int] = []
    for part in parts:
        if not part.isdigit():
            return None
        parsed.append(int(part))
    return tuple(parsed)


def _is_newer_version(candidate: str, current: str) -> bool:
    candidate_version = _parse_version(candidate)
    current_version = _parse_version(current)
    if candidate_version is None or current_version is None:
        return candidate.strip() != current.strip()
    return candidate_version > current_version


def _get_latest_release() -> Dict[str, Any]:
    response = request_with_retry(
        RELEASE_API_URL,
        headers={
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        exit_on_error=False,
        network_scope="update",
    )
    if response is None:
        raise RuntimeError("Could not load latest release metadata")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Invalid latest release metadata")
    return payload


def _open_release_page() -> None:
    try:
        opened = webbrowser.open(RELEASE_PAGE_URL)
        if not opened:
            print(t("Could not open browser. Please visit the following URL manually:"))
            print(RELEASE_PAGE_URL)
    except Exception:
        print(t("Could not open browser. Please visit the following URL manually:"))
        print(RELEASE_PAGE_URL)


def _missing_files() -> List[Path]:
    return [path for path in FILES_TO_CHECK if not path.exists() or not path.is_file()]


def ask_for_update() -> int:
    if STATUS_MODE:
        print(2)
        sys.exit()

    if Config.get("update_method") == "automatically":
        Config.set("update_method", "manual")
        print(
            color_text(
                t(
                    "Automatic in-place updates have been disabled for security reasons."
                ),
                "93",
            )
        )

    print(color_text(t("[UPDATE AVAILABLE]"), "93"))
    print(
        t(
            "Updates are applied only from a locally downloaded archive that you verify first."
        )
    )
    answer = input(t("Open the GitHub releases page now? (y/n): ")).strip().lower()
    if answer == "y":
        _open_release_page()
    return 1


def ask_for_update_consent() -> None:
    print(color_text(t("New Feature: Update Settings"), "93"))
    print(color_text(t("Please select how you want to handle updates:"), "93"))
    print(
        color_text(
            t(
                "- [m]anual update notifications: You will be told when a new verified release is available."
            ),
            "93",
        )
    )
    print(
        color_text(
            t("- [b]lock updates: Update checks will be disabled completely"), "93"
        )
    )
    print(
        color_text(
            t(
                'You can change your mind everytime by removing "update_method" from your "data/private/settings.json":'
            ),
            "93",
        )
    )
    consent = input(t("Please choose an option (m/b): ")).strip().lower()

    if consent == "b":
        Config.set("update_method", "block")
    else:
        Config.set("update_method", "manual")


def main() -> int:
    missing = _missing_files()
    if missing:
        if STATUS_MODE:
            print(2)
            sys.exit()
        print(t("[PACKAGE CORRUPT]"))
        print(
            t(
                "Your Project is missing some files. Please restore the complete local project or apply a verified update archive."
            )
        )
        for path in missing:
            print(t("[WARN] File missing: {path}").format(path=path))
        return ask_for_update()

    if not Config.has("update_method") or Config.get("update_method") == "":
        if STATUS_MODE:
            print(2)
            sys.exit()
        ask_for_update_consent()

    if Config.get("update_method") == "automatically":
        Config.set("update_method", "manual")
        if not STATUS_MODE:
            print(
                color_text(
                    t(
                        "Automatic in-place updates have been disabled for security reasons."
                    ),
                    "93",
                )
            )

    if Config.get("update_method") == "block":
        return 0

    try:
        latest_release = _get_latest_release()
    except Exception as e:
        if STATUS_MODE:
            print(-1)
            sys.exit()
        print(
            t("[ERROR] Could not load latest release information: {error}").format(
                error=e
            ),
            file=sys.stderr,
        )
        return 2

    latest_tag = str(latest_release.get("tag_name") or "").strip()
    if latest_tag and _is_newer_version(latest_tag, VERSION):
        if not STATUS_MODE:
            release_name = latest_release.get("name") or latest_tag
            print(t("Latest Release: {release}").format(release=release_name))
        return ask_for_update()

    return 0


if __name__ == "__main__":
    code = main()
    sys.exit(code)
