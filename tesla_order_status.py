#!/usr/bin/env python3
"""Entry point for the Tesla order status tool.

If anything goes wrong during startup, a hint is printed telling the
user to rerun the main CLI with --update.
"""

import sys
import traceback

from app.utils.params import get_args, set_args


def _prepare_cli_args():
    args = get_args()
    set_args(args)
    return args


def main() -> None:
    _prepare_cli_args()

    from app.legacy_compat import run_legacy_compatibility_migration
    from app.update import check_for_updates, maybe_run_update_from_main_cli

    maybe_run_update_from_main_cli()

    migration_changes = run_legacy_compatibility_migration()
    for change in migration_changes:
        print(f"> Compatibility migration: {change}")

    check_for_updates()

    """Import and run the application modules."""
    from app.utils.auth import main as run_tesla_auth
    from app.utils.orders import main as run_orders
    from app.utils.params import CACHED_MODE, STATUS_MODE

    if CACHED_MODE:
        access_token = None
    else:
        access_token = run_tesla_auth()
    run_orders(access_token)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 - catch-all for user guidance
        print(f"\n[ERROR] {e}\n")
        traceback.print_exc()
        print("\n\nYou can attempt to fix the installation by running:")
        print("python3 tesla_order_status.py --update")
        print(
            "\nIf the problem persists, please create an issue including the complete output of tesla_order_status.py"
        )
        print("GitHub Issues: https://github.com/enoch85/tesla-order-status/issues")
        sys.exit(1)
