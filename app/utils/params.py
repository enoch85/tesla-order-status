import argparse
import os
import time
from types import SimpleNamespace
from typing import Optional

from app.config import ORDERS_FILE
from app.utils.locale import t

_ARGS: Optional[argparse.Namespace] = None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Retrieve Tesla order status.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--status", action="store_true", help=t("HELP PARAM STATUS"))
    group.add_argument("--share", action="store_true", help=t("HELP PARAM SHARE"))
    group.add_argument("--details", action="store_true", help=t("HELP PARAM DETAILS"))
    group.add_argument("--all", action="store_true", help=t("HELP PARAM ALL"))
    group.add_argument(
        "--update",
        nargs="?",
        const="",
        metavar="ARCHIVE",
        help="Check, download, or apply updates using the main CLI.",
    )
    parser.add_argument("--sha256", help="Expected SHA-256 checksum for --update.")
    parser.add_argument("--cached", action="store_true", help=t("HELP PARAM CACHED"))
    parser.add_argument("--order", metavar="REFERENCE", help=t("HELP PARAM ORDER"))
    return parser


def _normalize_args(args: argparse.Namespace) -> argparse.Namespace:
    if not args.cached and os.path.exists(ORDERS_FILE):
        last_api_call = os.path.getmtime(ORDERS_FILE)
        if time.time() - last_api_call < 60:
            args.cached = True

    args.order_filter = (
        args.order.strip().upper()
        if isinstance(args.order, str) and args.order.strip()
        else None
    )
    return args


def get_args() -> argparse.Namespace:
    global _ARGS
    if _ARGS is None:
        _ARGS = _normalize_args(build_parser().parse_args())
    return _ARGS


def set_args(args: argparse.Namespace) -> argparse.Namespace:
    global _ARGS
    _ARGS = _normalize_args(args)
    return _ARGS


def _exported_value(name: str):
    args = get_args()
    mapping = {
        "DETAILS_MODE": args.details,
        "SHARE_MODE": args.share,
        "STATUS_MODE": args.status,
        "CACHED_MODE": args.cached,
        "ALL_KEYS_MODE": args.all,
        "ORDER_FILTER": args.order_filter,
        "UPDATE_MODE": args.update,
        "UPDATE_SHA256": args.sha256,
    }
    if name not in mapping:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return mapping[name]


def __getattr__(name: str):
    return _exported_value(name)


def defaults_namespace() -> SimpleNamespace:
    return SimpleNamespace(
        details=False,
        share=False,
        status=False,
        cached=False,
        all=False,
        order=None,
        order_filter=None,
        update=None,
        sha256=None,
    )
