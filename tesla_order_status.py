#!/usr/bin/env python3
"""Entry point for the Tesla order status tool.

If anything goes wrong during startup, a hint is printed telling the
user to run the standalone ``hotfix.py`` script with a manually
downloaded release archive.
"""

import sys
import traceback


def main() -> None:
    # Run all migrations
    from app.utils.migration import main as run_all_migrations

    run_all_migrations()

    # Run check for updates
    from app.update_check import main as run_update_check

    run_update_check()

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
        print("hotfix.py instead of tesla_order_status.py")
        print(
            "\nIf the problem persists, please create an issue including the complete output of tesla_order_status.py"
        )
        print("GitHub Issues: https://github.com/enoch85/tesla-order-status/issues")
        sys.exit(1)
