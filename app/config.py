import json
import os
import time
from pathlib import Path
from typing import Any, Dict

# -------------------------
# Constants
# -------------------------
TESLA_APP_VERSION = "4.53.1-4047"
TESLA_USER_AGENT = "Tesla/4.53.1 (com.teslamotors.tesla; build:4047; Android 14)"
TESLA_X_USER_AGENT = "TeslaApp/4.53.1-4047/4047/android/14"
TODAY = time.strftime("%Y-%m-%d")
TELEMETRIC_URL = "https://www.tesla-order-status-tracker.de/push/telemetry.php"
OPTION_CODES_URL = "https://www.tesla-order-status-tracker.de/push/option_codes.php"
VERSION = "2.0.0"
NETWORK_POLICY_MESSAGE = "Only Tesla API traffic and GitHub update checks are allowed. Telemetry and third-party data sharing are disabled."

# -------------------------
# Directory structure (new)
# -------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
APP_DIR = BASE_DIR / "app"
DATA_DIR = BASE_DIR / "data"
PUBLIC_DIR = DATA_DIR / "public"
PRIVATE_DIR = DATA_DIR / "private"

TOKEN_FILE = PRIVATE_DIR / "tesla_tokens.json"
ORDERS_FILE = PRIVATE_DIR / "tesla_orders.json"
HISTORY_FILE = PRIVATE_DIR / "tesla_order_history.json"
TESLA_STORES_FILE = PUBLIC_DIR / "tesla_locations.json"
SETTINGS_FILE = PRIVATE_DIR / "settings.json"


def _strip_trailing_commas(text: str) -> str:
    cleaned = []
    in_string = False
    escape = False

    for idx, char in enumerate(text):
        if in_string:
            cleaned.append(char)
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
            cleaned.append(char)
            continue

        if char == ",":
            look_ahead = idx + 1
            while look_ahead < len(text) and text[look_ahead].isspace():
                look_ahead += 1
            if look_ahead < len(text) and text[look_ahead] in "]}":
                continue

        cleaned.append(char)

    return "".join(cleaned)


def _set_private_permissions(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


# -------------------------
# Dataobjects
# -------------------------
try:
    with open(TESLA_STORES_FILE, encoding="utf-8") as f:
        TESLA_STORES = json.load(f)
except Exception:
    TESLA_STORES = {}


class Config:
    def __init__(self, path: Path):
        self._path = path
        self._cfg: Dict[str, Any] = {}
        self.load()  # gleich beim Init laden

    def load(self) -> None:
        if not self._path.exists():
            self._cfg = {}
            return
        try:
            with self._path.open(encoding="utf-8") as f:
                text = f.read()
                text = _strip_trailing_commas(text)
                self._cfg = json.loads(text)
        except json.JSONDecodeError as e:
            self._cfg = {}
            return

    def save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        text = (
            json.dumps(self._cfg, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
        )
        tmp = self._path.with_suffix(self._path.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(self._path)
        _set_private_permissions(self._path)

    def get(self, key: str, default: Any = None) -> Any:
        return self._cfg.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._cfg[key] = value
        self.save()

    def has(self, key: str) -> bool:
        return key in self._cfg

    def delete(self, key: str) -> None:
        self._cfg.pop(key, None)
        self.save()


cfg = Config(SETTINGS_FILE)
