"""Utility helpers for HTTP requests with retry logic."""

import json as jsonlib
import random
import time
from urllib.parse import urlparse
import requests
from typing import Dict, Union

from app.config import NETWORK_POLICY_MESSAGE
from app.utils.helpers import exit_with_status
from app.utils.locale import t

REQUEST_TIMEOUT = 15
MAX_RETRY_DELAY = 8
TESLA_ALLOWED_HOSTS = {
    "auth.tesla.com",
    "owner-api.teslamotors.com",
    "akamai-apigateway-vfx.tesla.com",
}
UPDATE_ALLOWED_HOSTS = {
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "raw.githubusercontent.com",
}


def _sleep_for_retry(attempt: int) -> None:
    delay = min(2**attempt, MAX_RETRY_DELAY)
    time.sleep(delay + random.uniform(0.0, 0.5))


def _is_local_url(url: str) -> bool:
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").lower()
    return hostname in {"", "localhost", "127.0.0.1", "::1"}


def _is_allowed_remote(url: str, network_scope: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    if network_scope == "tesla":
        return hostname in TESLA_ALLOWED_HOSTS
    if network_scope == "update":
        return hostname in UPDATE_ALLOWED_HOSTS
    return False


def request_with_retry(
    url,
    headers=None,
    data=None,
    json=None,
    max_retries=3,
    exit_on_error=True,
    network_scope="deny",
):
    """Perform a GET or POST request with exponential backoff retries.

    Parameters
    ----------
    url : str
        Target endpoint.
    headers : dict, optional
        Headers to include with the request.
    data : Any, optional
        Data payload for ``POST`` requests.
    json : Any, optional
        JSON payload for ``POST`` requests.
    max_retries : int
        Number of attempts before giving up.
    exit_on_error : bool
        When ``True`` (default) the function prints a user friendly message
        and terminates the program on failure. When ``False`` a ``RuntimeError``
        is raised instead so callers can handle network issues gracefully.
    """
    _STATUS_TEXTS: Dict[Union[int, str], str] = {
        400: t("400"),
        401: t("401"),
        403: t("403"),
        404: t("404"),
        422: t("422"),
        429: t("429"),
        "5xx": t("5xx"),
    }
    if not _is_local_url(url) and not _is_allowed_remote(url, network_scope):
        if exit_on_error:
            exit_with_status(NETWORK_POLICY_MESSAGE)
        raise RuntimeError(NETWORK_POLICY_MESSAGE)
    for attempt in range(max_retries):
        try:
            if data is None and json is None:
                response = requests.get(
                    url, headers=headers, timeout=REQUEST_TIMEOUT, verify=True
                )
            else:
                if json is not None:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=json,
                        timeout=REQUEST_TIMEOUT,
                        verify=True,
                    )
                else:
                    # Falls string/bytes: direkt senden; falls dict: sauber als JSON senden
                    if isinstance(data, (dict, list)):
                        response = requests.post(
                            url,
                            headers={
                                "Content-Type": "application/json",
                                **(headers or {}),
                            },
                            data=jsonlib.dumps(data, separators=(",", ":")),
                            timeout=REQUEST_TIMEOUT,
                            verify=True,
                        )
                    else:
                        response = requests.post(
                            url,
                            headers=headers,
                            data=data,
                            timeout=REQUEST_TIMEOUT,
                            verify=True,
                        )

            try:
                response.raise_for_status()
            except Exception:
                if response.status_code >= 500:
                    if attempt == max_retries - 1:
                        if exit_on_error:
                            exit_with_status(_STATUS_TEXTS["5xx"])
                        else:
                            raise RuntimeError(_STATUS_TEXTS["5xx"])

                    _sleep_for_retry(attempt)
                    continue
                else:
                    error_text = _STATUS_TEXTS.get(
                        response.status_code, _STATUS_TEXTS["5xx"]
                    )
                    if exit_on_error:
                        exit_with_status(error_text)
                    else:
                        raise RuntimeError(error_text)

            return response
        except requests.exceptions.RequestException:
            if attempt == max_retries - 1:
                if exit_on_error:
                    exit_with_status(_STATUS_TEXTS["5xx"])
                else:
                    raise RuntimeError(_STATUS_TEXTS["5xx"])
            _sleep_for_retry(attempt)
    return None
