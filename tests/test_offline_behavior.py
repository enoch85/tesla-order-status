import json
import unittest
from unittest.mock import patch

from app.config import _strip_trailing_commas
from app.utils import option_codes as option_codes_module
from app.utils.connection import _is_allowed_remote, _is_local_url
from app.utils.option_codes import _normalize_entry, _parse_timestamp


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

    def test_parse_timestamp_supports_zulu_and_naive_formats(self):
        zulu_timestamp = _parse_timestamp("2026-03-11T19:03:41Z")
        naive_timestamp = _parse_timestamp("2025-10-16 15:49:52")

        self.assertIsNotNone(zulu_timestamp)
        self.assertIsNotNone(naive_timestamp)
        self.assertEqual(zulu_timestamp.isoformat(), "2026-03-11T19:03:41+00:00")
        self.assertEqual(naive_timestamp.isoformat(), "2025-10-16T15:49:52+00:00")


class OfflineCatalogTests(unittest.TestCase):
    def test_complete_local_option_catalog_loads_recent_entries(self):
        with patch.object(option_codes_module, "_OPTION_CODES", None), patch.object(
            option_codes_module, "_load_cache", return_value=None
        ), patch.object(
            option_codes_module, "_fetch_remote", return_value=(None, None)
        ):
            option_codes = option_codes_module.get_option_codes(force_refresh=True)

        self.assertGreaterEqual(len(option_codes), 794)
        self.assertEqual(option_codes["APBS"]["label"], "Autopilot")
        self.assertEqual(option_codes["IBB5"]["label"], "All Black")
        self.assertEqual(option_codes["VC01"]["label"], "MCU AMD Ryzen")
        self.assertEqual(option_codes["MTC07"]["label"], "Cybertruck AWD")
        self.assertEqual(
            option_codes["WY19P"]["label"], '19" Crossflow wheels (Model Y Juniper)'
        )


if __name__ == "__main__":
    unittest.main()
