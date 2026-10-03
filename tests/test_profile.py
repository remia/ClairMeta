# Clairmeta - (C) YMAGIS S.A.
# See LICENSE for more information

import os
import unittest

from clairmeta.profile import get_default_profile, load_profile, save_profile
from clairmeta.utils.file import temporary_file


class ProfileTest(unittest.TestCase):
    def get_file_path(self, name):
        file_path = os.path.join(os.path.dirname(__file__), "resources", name)

        return file_path

    def test_load_profile(self):
        p = load_profile(self.get_file_path("myprofile.json"))
        self.assertEqual(p["log_level"], "INFO")
        self.assertEqual(p["bypass"], ["check_assets_pkl_hash"])
        self.assertEqual(p["criticality"]["default"], "ERROR")

    def test_save_profile(self):
        with temporary_file(suffix=".json") as f:
            p_gold = get_default_profile()
            save_profile(p_gold, f)
            p = load_profile(f)
            self.assertEqual(p, p_gold)


if __name__ == "__main__":
    unittest.main()
