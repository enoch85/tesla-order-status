#!/usr/bin/env python3
"""Apply a locally downloaded release archive after validating its contents."""

import hashlib
import os
import shutil
import sys
import tempfile
import traceback
import zipfile
from pathlib import Path


def _copytree_compat(src: Path, dst: Path) -> None:
    """Recursively copy directories without relying on dirs_exist_ok."""
    if sys.version_info >= (3, 8):
        shutil.copytree(src, dst, dirs_exist_ok=True)
        return

    if dst.exists() and not dst.is_dir():
        raise ValueError(f"Target path {dst} exists and is not a directory")
    dst.mkdir(parents=True, exist_ok=True)
    for child in src.iterdir():
        target = dst / child.name
        if child.is_dir():
            _copytree_compat(child, target)
        else:
            shutil.copy2(child, target)


RELEASES_URL = "https://github.com/chrisi51/tesla-order-status/releases/latest"


def _is_within_directory(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath([str(root), str(candidate)]) == str(root)
    except ValueError:
        return False


def _is_symlink(member: zipfile.ZipInfo) -> bool:
    return ((member.external_attr >> 16) & 0o170000) == 0o120000


def _safe_extract_zip(zf: zipfile.ZipFile, target_dir: Path) -> None:
    root = target_dir.resolve()
    for member in zf.infolist():
        if not member.filename:
            continue
        target_path = (target_dir / member.filename).resolve()
        if not _is_within_directory(root, target_path):
            raise ValueError(f"Unsafe archive entry: {member.filename}")
        if _is_symlink(member):
            raise ValueError(f"Symlink entries are not allowed: {member.filename}")
        if member.is_dir():
            target_path.mkdir(parents=True, exist_ok=True)
            continue
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with zf.open(member) as source, open(target_path, "wb") as destination:
            shutil.copyfileobj(source, destination)


def _get_archive_path() -> Path:
    if len(sys.argv) > 1:
        return Path(sys.argv[1]).expanduser()
    archive_path = input("Enter the path to a locally downloaded release ZIP: ").strip()
    if not archive_path:
        raise ValueError("No archive path provided")
    return Path(archive_path).expanduser()


def _compute_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _extract_sha256(text: str, archive_name: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) == 1 and len(parts[0]) == 64:
            return parts[0].lower()
        if len(parts) >= 2 and len(parts[0]) == 64:
            candidate_name = parts[-1].lstrip("*./")
            if candidate_name == archive_name:
                return parts[0].lower()
    raise ValueError("No valid SHA-256 checksum found")


def _get_expected_sha256(archive_path: Path) -> str:
    if len(sys.argv) > 2:
        provided = sys.argv[2].strip().lower()
        if len(provided) == 64:
            return provided
        raise ValueError("Provided SHA-256 checksum must be a 64-character hex string")

    sidecar_candidates = [
        archive_path.with_suffix(archive_path.suffix + ".sha256"),
        archive_path.with_suffix(".sha256"),
        archive_path.with_suffix(archive_path.suffix + ".sha256sum"),
    ]
    for sidecar in sidecar_candidates:
        if sidecar.exists() and sidecar.is_file():
            return _extract_sha256(
                sidecar.read_text(encoding="utf-8"), archive_path.name
            )

    provided = (
        input(
            "Enter the expected SHA-256 checksum for this archive (required, 64 hex chars): "
        )
        .strip()
        .lower()
    )
    if len(provided) == 64:
        return provided
    raise ValueError("A valid SHA-256 checksum is required to apply the update archive")


def main() -> None:
    print("This script no longer downloads code from the network.")
    print("Download a verified release ZIP manually and provide its path here.")
    print(f"Latest releases: {RELEASES_URL}")
    answer = (
        input("Do you want to apply a local hotfix archive? (y/n): ").strip().lower()
    )
    if answer != "y":
        print("\nHotfix canceled...")
        sys.exit(1)

    try:
        archive_path = _get_archive_path()
        if not archive_path.exists() or not archive_path.is_file():
            raise FileNotFoundError(f"Archive not found: {archive_path}")
        expected_sha256 = _get_expected_sha256(archive_path)
        actual_sha256 = _compute_sha256(archive_path)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                "Archive checksum mismatch. "
                f"Expected {expected_sha256}, got {actual_sha256}"
            )

        print("\nValidating and extracting archive...")
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            with zipfile.ZipFile(archive_path) as zf:
                _safe_extract_zip(zf, tmp_path)

            extracted_dirs = [path for path in tmp_path.iterdir() if path.is_dir()]
            if len(extracted_dirs) != 1:
                raise ValueError(
                    "Expected a single top-level directory inside the archive"
                )
            extracted_dir = extracted_dirs[0]
            for item in extracted_dir.iterdir():
                target = Path(".") / item.name
                if item.is_dir():
                    _copytree_compat(item, target)
                else:
                    shutil.copy2(item, target)
        print("...Hotfix applied. Please rerun tesla_order_status.py")
        print(
            "\nIf the problem persists, please create an issue including the complete output of tesla_order_status.py"
        )
        print("GitHub Issues: https://github.com/chrisi51/tesla-order-status/issues")

    except Exception as e:  # noqa: BLE001 - best effort, minimal deps
        print(f"...Hotfix failed: {e}\n")
        traceback.print_exc()
        print(
            "\nIf the problem persists, please create an issue including the complete output of hotfix.py"
        )
        print("GitHub Issues: https://github.com/chrisi51/tesla-order-status/issues")
        sys.exit(1)


if __name__ == "__main__":
    main()
