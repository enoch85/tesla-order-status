import base64
import getpass
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import _set_private_permissions
from app.utils.locale import t

TOKEN_PASSPHRASE_ENV = "TESLA_ORDER_STATUS_TOKEN_PASSPHRASE"
TOKEN_ENVELOPE_MARKER = "__tesla_order_status_encrypted__"
TOKEN_ENVELOPE_VERSION = 1
_RUNTIME_PASSPHRASE_UNSET = object()
_runtime_token_passphrase: object = _RUNTIME_PASSPHRASE_UNSET


class TokenStorageError(RuntimeError):
    pass


def set_runtime_token_passphrase(passphrase: Optional[str]) -> None:
    global _runtime_token_passphrase
    if passphrase is None:
        _runtime_token_passphrase = None
        return
    normalized = passphrase.strip()
    _runtime_token_passphrase = normalized or None


def clear_runtime_token_passphrase() -> None:
    global _runtime_token_passphrase
    _runtime_token_passphrase = _RUNTIME_PASSPHRASE_UNSET


def _prompt_for_token_passphrase(path: Path) -> str:
    if not sys.stdin.isatty():
        raise TokenStorageError(
            t(
                "Encrypted Tesla tokens were found at '{file}', but TESLA_ORDER_STATUS_TOKEN_PASSPHRASE is not set."
            ).format(file=path)
        )

    passphrase = getpass.getpass("Token passphrase: ")
    normalized = passphrase.strip()
    if not normalized:
        raise TokenStorageError("Token passphrase prompt was empty.")
    set_runtime_token_passphrase(normalized)
    return normalized


def _get_token_passphrase() -> Optional[str]:
    if _runtime_token_passphrase is not _RUNTIME_PASSPHRASE_UNSET:
        return _runtime_token_passphrase  # type: ignore[return-value]

    passphrase = os.environ.get(TOKEN_PASSPHRASE_ENV)
    if passphrase is None:
        return None
    passphrase = passphrase.strip()
    return passphrase or None


def token_encryption_enabled() -> bool:
    return _get_token_passphrase() is not None


def _load_crypto_primitives():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    except ImportError as exc:
        raise TokenStorageError(
            t(
                "Token encryption was requested, but the 'cryptography' package is not installed. Install it with 'python3 -m pip install cryptography' or remove TESLA_ORDER_STATUS_TOKEN_PASSPHRASE."
            )
        ) from exc
    return AESGCM, Scrypt


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


def _is_encrypted_payload(payload: Any) -> bool:
    return isinstance(payload, dict) and payload.get(TOKEN_ENVELOPE_MARKER) is True


def _encrypt_tokens(tokens: Dict[str, Any], passphrase: str) -> Dict[str, Any]:
    AESGCM, Scrypt = _load_crypto_primitives()
    salt = os.urandom(16)
    nonce = os.urandom(12)
    kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
    key = kdf.derive(passphrase.encode("utf-8"))
    plaintext = json.dumps(tokens, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    return {
        TOKEN_ENVELOPE_MARKER: True,
        "version": TOKEN_ENVELOPE_VERSION,
        "cipher": "AES-256-GCM",
        "kdf": "scrypt",
        "salt": _b64encode(salt),
        "nonce": _b64encode(nonce),
        "ciphertext": _b64encode(ciphertext),
    }


def _decrypt_tokens(
    payload: Dict[str, Any], passphrase: str, path: Path
) -> Dict[str, Any]:
    AESGCM, Scrypt = _load_crypto_primitives()
    try:
        salt = _b64decode(str(payload["salt"]))
        nonce = _b64decode(str(payload["nonce"]))
        ciphertext = _b64decode(str(payload["ciphertext"]))
    except Exception as exc:
        raise TokenStorageError(
            t("Encrypted token storage at '{file}' is malformed.").format(file=path)
        ) from exc

    try:
        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
        key = kdf.derive(passphrase.encode("utf-8"))
        plaintext = AESGCM(key).decrypt(nonce, ciphertext, None)
        tokens = json.loads(plaintext.decode("utf-8"))
    except Exception as exc:
        raise TokenStorageError(
            t(
                "Could not decrypt Tesla tokens from '{file}'. Verify TESLA_ORDER_STATUS_TOKEN_PASSPHRASE."
            ).format(file=path)
        ) from exc

    if not isinstance(tokens, dict):
        raise TokenStorageError(
            t("Decrypted token storage at '{file}' is not a JSON object.").format(
                file=path
            )
        )
    return tokens


def save_token_data(path: Path, tokens: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: Dict[str, Any]
    passphrase = _get_token_passphrase()
    if passphrase is None:
        payload = tokens
    else:
        payload = _encrypt_tokens(tokens, passphrase)

    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    _set_private_permissions(tmp)
    tmp.replace(path)
    _set_private_permissions(path)


def load_token_data(path: Path) -> Dict[str, Any]:
    _set_private_permissions(path)
    with path.open(encoding="utf-8") as file_handle:
        payload = json.load(file_handle)

    if _is_encrypted_payload(payload):
        passphrase = _get_token_passphrase()
        if passphrase is None:
            passphrase = _prompt_for_token_passphrase(path)
        return _decrypt_tokens(payload, passphrase, path)

    if not isinstance(payload, dict):
        raise ValueError("Token storage file did not contain a JSON object")

    return payload
