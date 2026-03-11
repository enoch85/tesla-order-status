import base64
import hashlib
import json
import os
import urllib.parse
import sys
import webbrowser
from typing import Any, Dict, Optional

from app.config import TOKEN_FILE
from app.utils.colors import color_text
from app.utils.connection import request_with_retry
from app.utils.helpers import exit_with_status
from app.utils.locale import t
from app.utils.params import STATUS_MODE
from app.utils.token_storage import (
    TokenStorageError,
    load_token_data,
    save_token_data,
    token_encryption_enabled,
)

CLIENT_ID = "ownerapi"
REDIRECT_URI = "https://auth.tesla.com/void/callback"
AUTH_URL = "https://auth.tesla.com/oauth2/v3/authorize"
TOKEN_URL = "https://auth.tesla.com/oauth2/v3/token"
SCOPE = "openid email offline_access"
CODE_CHALLENGE_METHOD = "S256"


def _generate_auth_state() -> str:
    return os.urandom(16).hex()


def _generate_code_verifier_and_challenge():
    code_verifier = (
        base64.urlsafe_b64encode(os.urandom(32)).rstrip(b"=").decode("utf-8")
    )
    code_challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("utf-8")).digest())
        .rstrip(b"=")
        .decode("utf-8")
    )
    return code_verifier, code_challenge


def _get_auth_code(code_challenge: str, expected_state: str):
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPE,
        "state": expected_state,
        "code_challenge": code_challenge,
        "code_challenge_method": CODE_CHALLENGE_METHOD,
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(auth_params)}"
    print(
        color_text(
            t(
                "To retrieve your order status, you need to authenticate with your Tesla account."
            ),
            "93",
        )
    )
    message_parts = [
        color_text(
            t(
                "A browser window will open with the Tesla login page. After logging in you will likely see a"
            ),
            93,
        ),
        color_text(t('"Page Not Found"'), 91),
        color_text(t("page."), 93),
        color_text(t("That is CORRECT!"), 91),
    ]
    print(" ".join(message_parts))
    print(
        color_text(
            t(
                "Copy the full URL of that page and return here. The authentication happens only between you and Tesla; no data leaves your system."
            ),
            "93",
        )
    )
    if (
        input(color_text(t("Proceed to open the login page? (y/n): "), "93")).lower()
        != "y"
    ):
        print(color_text(t("Authentication cancelled."), "91"))
        sys.exit(0)
    try:
        if not webbrowser.open(auth_url):
            print(color_text(t("No GUI detected. Open this URL manually:"), 91))
            print(f"{auth_url}")
    except Exception:
        print(color_text(t("No GUI detected. Open this URL manually:"), 91))
        print(f"{auth_url}")
    redirected_url = input(
        color_text(t("Please enter the redirected URL here: "), "93")
    )
    parsed_url = urllib.parse.urlparse(redirected_url)
    params = urllib.parse.parse_qs(parsed_url.query)
    returned_state = params.get("state", [None])[0]
    if returned_state != expected_state:
        exit_with_status(
            t(
                "The OAuth state returned by Tesla did not match. Please retry the login flow."
            )
        )
    code = params.get("code")
    if not code:
        exit_with_status(t("No authentication code found in the redirected URL."))
    return code[0]


def _exchange_code_for_tokens(auth_code, code_verifier):
    token_data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    response = request_with_retry(TOKEN_URL, None, token_data, network_scope="tesla")
    return response.json()


def _save_tokens_to_file(tokens: Dict[str, Any]):
    save_token_data(TOKEN_FILE, tokens)
    if not STATUS_MODE:
        message = "> Tokens saved to '{file}'"
        if token_encryption_enabled():
            message = "> Tokens encrypted and saved to '{file}'"
        print(color_text(t(message).format(file=TOKEN_FILE), "94"))


def _load_tokens_from_file():
    return load_token_data(TOKEN_FILE)


def _merge_token_response(
    token_response: Dict[str, Any], existing_tokens: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    if not isinstance(token_response, dict) or "access_token" not in token_response:
        raise ValueError("Token response did not contain an access token")
    merged = dict(existing_tokens or {})
    merged.update(token_response)
    if (
        existing_tokens
        and "refresh_token" not in merged
        and existing_tokens.get("refresh_token")
    ):
        merged["refresh_token"] = existing_tokens["refresh_token"]
    return merged


def _is_reauthentication_error(message: str) -> bool:
    return message in {t("400"), t("401"), t("422")}


def _refresh_tokens(refresh_token):
    token_data = {
        "grant_type": "refresh_token",
        "client_id": CLIENT_ID,
        "refresh_token": refresh_token,
    }
    response = request_with_retry(
        TOKEN_URL, None, token_data, exit_on_error=False, network_scope="tesla"
    )
    return response.json()


def _authenticate_interactively(
    code_verifier: str, code_challenge: str
) -> Dict[str, Any]:
    auth_state = _generate_auth_state()
    token_response = _exchange_code_for_tokens(
        _get_auth_code(code_challenge, auth_state), code_verifier
    )
    return _merge_token_response(token_response)


# ---------------------------
# Main-Logic
# ---------------------------
def main() -> str:
    code_verifier, code_challenge = _generate_code_verifier_and_challenge()

    if os.path.exists(TOKEN_FILE):
        try:
            token_file = _load_tokens_from_file()
            refresh_token = token_file["refresh_token"]
            if not STATUS_MODE:
                print(color_text(t("> Refreshing saved Tesla tokens..."), "94"))
            refreshed_tokens = _merge_token_response(
                _refresh_tokens(refresh_token), token_file
            )
            _save_tokens_to_file(refreshed_tokens)
            access_token = refreshed_tokens["access_token"]

        except RuntimeError as e:
            if STATUS_MODE:
                print(-1)
                sys.exit(0)
            if _is_reauthentication_error(str(e)):
                print(
                    color_text(
                        t("> Saved tokens are no longer usable. Re-authenticating..."),
                        "94",
                    )
                )
                refreshed_tokens = _authenticate_interactively(
                    code_verifier, code_challenge
                )
                access_token = refreshed_tokens["access_token"]
                _save_tokens_to_file(refreshed_tokens)
            else:
                exit_with_status(str(e))
        except TokenStorageError as e:
            if STATUS_MODE:
                print(-1)
                sys.exit(0)
            exit_with_status(str(e))
        except (json.JSONDecodeError, KeyError, ValueError):
            if not STATUS_MODE:
                print(
                    color_text(
                        t("> Error loading tokens from file. Re-authenticating..."),
                        "94",
                    )
                )
                refreshed_tokens = _authenticate_interactively(
                    code_verifier, code_challenge
                )
                access_token = refreshed_tokens["access_token"]
                _save_tokens_to_file(refreshed_tokens)
            else:
                print(-1)
                sys.exit(0)

    else:
        if not STATUS_MODE:
            token_response = _authenticate_interactively(code_verifier, code_challenge)
            access_token = token_response["access_token"]
            if (
                input(
                    color_text(
                        t(
                            "Would you like to save the tokens to '{file}' for use in future requests? (y/n): "
                        ).format(file=TOKEN_FILE),
                        "93",
                    )
                ).lower()
                == "y"
            ):
                _save_tokens_to_file(token_response)
        else:
            print(-1)
            sys.exit(0)

    return access_token
