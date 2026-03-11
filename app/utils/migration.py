import json
import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import List
from app.config import APP_DIR, PRIVATE_DIR

# -------------------------
# Migration runner
# -------------------------
MIGRATIONS_DIR = APP_DIR / "migrations"
MIGRATIONS_APPLIED_FILE = PRIVATE_DIR / "migrations_applied.json"
TRUSTED_MIGRATIONS = {
    "2025-08-23-history.py": "313f2337f524d7c02f41f5071de5add14ce1598b3624763d7c0c3c73922b86d9",
    "2025-08-30-datafolders.py": "d8b318ed804e0090e0600ca854a88e25a2d5ee7928ea8631ad1399785ee53377",
    "2025-09-15-history-trimvalues.py": "4890f81943f567e59e808991b2134f8220ea175436a3371bbae091f122621e09",
    "2025-11-12-history-reference.py": "27fdc7468acda408d701d99b9e3a91e6693ee2fd9cc1dc799fda7309f42b298f",
    "2025-11-12-orders-map.py": "dc8bf2af9b9787236d7b26a7ed30707d11fcb61a909a679308fb0ad981732cff",
}
PRIVATE_DIR.mkdir(parents=True, exist_ok=True)


def _set_private_permissions(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _verify_migration(path: Path) -> str:
    resolved_dir = MIGRATIONS_DIR.resolve()
    resolved_path = path.resolve()
    if path.is_symlink() or resolved_path.parent != resolved_dir:
        return "migration path is not trusted"
    expected_hash = TRUSTED_MIGRATIONS.get(path.name)
    if expected_hash is None:
        return "migration is not in the trusted allowlist"
    if _sha256_file(resolved_path) != expected_hash:
        return "migration hash does not match the trusted allowlist"
    return ""


def _load_applied_migrations() -> List[str]:
    if MIGRATIONS_APPLIED_FILE.exists():
        try:
            with open(MIGRATIONS_APPLIED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return []


def _save_applied_migrations(names: List[str]) -> None:
    with open(MIGRATIONS_APPLIED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(names), f)
    _set_private_permissions(MIGRATIONS_APPLIED_FILE)


def main() -> None:
    if not MIGRATIONS_DIR.exists():
        return
    applied = set(_load_applied_migrations())
    files = sorted(MIGRATIONS_DIR.glob("*.py"))
    for path in files:
        name = path.stem
        if name in applied:
            continue
        verification_error = _verify_migration(path)
        if verification_error:
            print(
                f"> Migration '{path.name}' skipped: {verification_error}",
                file=sys.stderr,
            )
            continue
        try:
            spec = importlib.util.spec_from_file_location(f"migrations.{name}", path)
            module = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            assert spec and spec.loader
            spec.loader.exec_module(module)  # type: ignore[union-attr]
            if hasattr(module, "run"):
                module.run()
            applied.add(name)
        except Exception as e:
            # Don't hard-fail, just report
            print(f"> Migration '{name}' failed: {e}", file=sys.stderr)
    _save_applied_migrations(list(applied))
