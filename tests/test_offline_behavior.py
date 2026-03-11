import json
import os
import tempfile
import unittest
from io import StringIO
from unittest import mock

from app.legacy_compat import migrate_legacy_history, migrate_legacy_layout
from app.config import _strip_trailing_commas
from app.update import _select_release_archive, _select_release_checksum_asset
from app.utils.connection import _is_allowed_remote, _is_local_url
from app.utils import orders as orders_module
from app.utils.option_codes import _normalize_entry, get_option_codes


class ConfigHelperTests(unittest.TestCase):
    def test_strip_trailing_commas_keeps_string_content(self):
        raw_text = (
            '{"items": [1, 2,], "nested": {"value": true,}, '
            '"note": "comma, stays inside string",}'
        )

        cleaned = _strip_trailing_commas(raw_text)

        self.assertEqual(
            json.loads(cleaned),
            {
                "items": [1, 2],
                "nested": {"value": True},
                "note": "comma, stays inside string",
            },
        )


class ConnectionPolicyTests(unittest.TestCase):
    def test_network_policy_helpers_respect_allowlists(self):
        self.assertTrue(_is_local_url("http://localhost:8080/health"))
        self.assertTrue(_is_local_url("https://127.0.0.1:4443/status"))
        self.assertTrue(
            _is_allowed_remote("https://auth.tesla.com/oauth2/v3/authorize", "tesla")
        )
        self.assertTrue(
            _is_allowed_remote(
                "https://api.github.com/repos/enoch85/tesla-order-status/releases",
                "update",
            )
        )
        self.assertFalse(
            _is_allowed_remote(
                "https://www.tesla-order-status-tracker.de/get/option_codes.php",
                "tesla",
            )
        )
        self.assertFalse(_is_allowed_remote("https://example.com", "update"))


class OptionCodeHelperTests(unittest.TestCase):
    def test_normalize_entry_uses_nested_raw_payload(self):
        normalized = _normalize_entry(
            {
                "category": "Interiors",
                "raw": {
                    "label_en": "Premium-Black (Premium AWD LR)",
                    "label_en_short": "Premium-Black",
                },
            }
        )

        self.assertEqual(
            normalized,
            {
                "label": "Premium-Black (Premium AWD LR)",
                "category": "interiors",
                "label_short": "Premium-Black",
                "raw": {
                    "label_en": "Premium-Black (Premium AWD LR)",
                    "label_en_short": "Premium-Black",
                },
            },
        )


class UpdateReleaseHelperTests(unittest.TestCase):
    def test_select_release_archive_prefers_zip_asset(self):
        release = {
            "tag_name": "2.0.0",
            "zipball_url": "https://api.github.com/repos/enoch85/tesla-order-status/zipball/2.0.0",
            "assets": [
                {
                    "name": "tesla-order-status-2.0.0.zip",
                    "browser_download_url": "https://github.com/enoch85/tesla-order-status/releases/download/2.0.0/tesla-order-status-2.0.0.zip",
                },
                {
                    "name": "tesla-order-status-2.0.0.zip.sha256",
                    "browser_download_url": "https://github.com/enoch85/tesla-order-status/releases/download/2.0.0/tesla-order-status-2.0.0.zip.sha256",
                },
            ],
        }

        archive = _select_release_archive(release)
        checksum = _select_release_checksum_asset(release, archive["name"])

        self.assertEqual(archive["name"], "tesla-order-status-2.0.0.zip")
        self.assertIsNotNone(checksum)
        self.assertEqual(checksum["name"], "tesla-order-status-2.0.0.zip.sha256")

    def test_select_release_archive_falls_back_to_zipball(self):
        release = {
            "tag_name": "2.0.0",
            "zipball_url": "https://api.github.com/repos/enoch85/tesla-order-status/zipball/2.0.0",
            "assets": [],
        }

        archive = _select_release_archive(release)

        self.assertEqual(archive["name"], "tesla-order-status-2.0.0.zip")
        self.assertEqual(archive["url"], release["zipball_url"])


class OfflineCatalogTests(unittest.TestCase):
    def test_complete_local_option_catalog_loads_recent_entries(self):
        option_codes = get_option_codes(force_refresh=True)

        self.assertGreaterEqual(len(option_codes), 794)
        self.assertEqual(option_codes["APBS"]["label"], "Autopilot")
        self.assertEqual(option_codes["IBB5"]["label"], "All Black")
        self.assertEqual(option_codes["VC01"]["label"], "MCU AMD Ryzen")
        self.assertEqual(option_codes["MTC07"]["label"], "Cybertruck AWD")
        self.assertEqual(
            option_codes["WY19P"]["label"], '19" Crossflow wheels (Model Y Juniper)'
        )

    def test_force_refresh_reloads_local_catalog(self):
        first_load = get_option_codes(force_refresh=True)
        second_load = get_option_codes(force_refresh=True)

        self.assertIsNot(first_load, second_load)


class ShareModeTests(unittest.TestCase):
    def test_bottom_line_recommends_pyperclip_install_when_missing(self):
        output = StringIO()

        with mock.patch.object(orders_module, "SHARE_MODE", True), mock.patch.object(
            orders_module, "HAS_PYPERCLIP", False
        ), mock.patch("sys.stdout", output):
            orders_module.print_bottom_line()

        rendered = output.getvalue()
        self.assertIn("pyperclip", rendered)
        self.assertIn("python3 -m pip install pyperclip", rendered)


class LegacyCompatibilityTests(unittest.TestCase):
    def test_migrate_legacy_layout_moves_root_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from app import legacy_compat

            base_dir = legacy_compat.BASE_DIR
            private_dir = legacy_compat.PRIVATE_DIR
            public_dir = legacy_compat.PUBLIC_DIR
            token_file = legacy_compat.TOKEN_FILE

            legacy_compat.BASE_DIR = legacy_compat.Path(tmpdir)
            legacy_compat.PRIVATE_DIR = legacy_compat.BASE_DIR / "data" / "private"
            legacy_compat.PUBLIC_DIR = legacy_compat.BASE_DIR / "data" / "public"
            legacy_compat.TOKEN_FILE = legacy_compat.PRIVATE_DIR / "tesla_tokens.json"
            legacy_compat.ORDERS_FILE = legacy_compat.PRIVATE_DIR / "tesla_orders.json"
            legacy_compat.HISTORY_FILE = (
                legacy_compat.PRIVATE_DIR / "tesla_order_history.json"
            )
            legacy_compat.SETTINGS_FILE = legacy_compat.PRIVATE_DIR / "settings.json"

            try:
                source = legacy_compat.BASE_DIR / "tesla_tokens.json"
                source.write_text('{"refresh_token": "secret"}\n', encoding="utf-8")

                changes = migrate_legacy_layout()

                self.assertTrue(any("tesla_tokens.json" in item for item in changes))
                self.assertFalse(source.exists())
                self.assertTrue(legacy_compat.TOKEN_FILE.exists())
            finally:
                legacy_compat.BASE_DIR = base_dir
                legacy_compat.PRIVATE_DIR = private_dir
                legacy_compat.PUBLIC_DIR = public_dir
                legacy_compat.TOKEN_FILE = token_file

    def test_migrate_legacy_history_converts_list_to_reference_map(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            from app import legacy_compat

            private_dir = legacy_compat.PRIVATE_DIR
            orders_file = legacy_compat.ORDERS_FILE
            history_file = legacy_compat.HISTORY_FILE

            legacy_compat.PRIVATE_DIR = legacy_compat.Path(tmpdir)
            legacy_compat.ORDERS_FILE = legacy_compat.PRIVATE_DIR / "tesla_orders.json"
            legacy_compat.HISTORY_FILE = (
                legacy_compat.PRIVATE_DIR / "tesla_order_history.json"
            )

            try:
                legacy_compat.PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
                legacy_compat.ORDERS_FILE.write_text(
                    json.dumps([{"referenceNumber": "RN123456"}]), encoding="utf-8"
                )
                legacy_compat.HISTORY_FILE.write_text(
                    json.dumps(
                        [
                            {
                                "key": "0.status",
                                "value": "BOOKED",
                            }
                        ]
                    ),
                    encoding="utf-8",
                )

                changed = migrate_legacy_history()
                migrated = json.loads(
                    legacy_compat.HISTORY_FILE.read_text(encoding="utf-8")
                )

                self.assertTrue(changed)
                self.assertIn("RN123456", migrated)
                self.assertEqual(migrated["RN123456"][0]["key"], "status")
                self.assertEqual(migrated["RN123456"][0]["order_reference"], "RN123456")
            finally:
                legacy_compat.PRIVATE_DIR = private_dir
                legacy_compat.ORDERS_FILE = orders_file
                legacy_compat.HISTORY_FILE = history_file


if __name__ == "__main__":
    unittest.main()
