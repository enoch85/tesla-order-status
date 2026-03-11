import json
import unittest

from app.config import _strip_trailing_commas
from app.utils.connection import _is_allowed_remote, _is_local_url
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


if __name__ == "__main__":
    unittest.main()
