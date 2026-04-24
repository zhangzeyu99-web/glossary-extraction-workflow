from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

from openpyxl import Workbook, load_workbook


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "extract_glossary.py"
SPEC = importlib.util.spec_from_file_location("extract_glossary", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class UtilityTests(unittest.TestCase):
    def test_normalize_english_ignores_case_spacing_and_plural(self):
        self.assertEqual(
            MODULE.normalize_english_for_compare("Rewards"),
            MODULE.normalize_english_for_compare("reward"),
        )
        self.assertEqual(
            MODULE.normalize_english_for_compare("Dual Guns"),
            MODULE.normalize_english_for_compare("dual   guns"),
        )

    def test_collect_translation_diff_marks_manual_adaptation(self):
        counter = MODULE.Counter(
            {
                "Sign Up": 3,
                "Registration": 2,
                "Registration Countdown": 1,
            }
        )
        diff = MODULE.collect_translation_diff("Sign Up", counter)
        self.assertEqual(diff["has_diff"], "Yes")
        self.assertEqual(diff["same_or_format_only_count"], 3)
        self.assertEqual(diff["diff_count"], 3)
        self.assertEqual(diff["diff_variants"], "Registration (2) | Registration Countdown (1)")

    def test_collect_translation_diff_ignores_context_extension(self):
        counter = MODULE.Counter(
            {
                "Registration": 2,
                "Registration Countdown": 2,
                "Registration Requirements": 1,
            }
        )
        diff = MODULE.collect_translation_diff("Registration", counter)
        self.assertEqual(diff["has_diff"], "No")
        self.assertEqual(diff["same_or_format_only_count"], 5)
        self.assertEqual(diff["diff_count"], 0)

    def test_split_usage_buckets_separates_example_and_manual_adaptation(self):
        counter = MODULE.Counter(
            {
                "Registration": 2,
                "Registration Countdown": 2,
                "Sign Up": 1,
                "Registered": 1,
            }
        )
        example_counter, manual_counter = MODULE.split_usage_buckets("Registration", counter)
        self.assertEqual(example_counter["Registration"], 2)
        self.assertEqual(example_counter["Registration Countdown"], 2)
        self.assertEqual(manual_counter["Sign Up"], 1)
        self.assertEqual(manual_counter["Registered"], 1)

    def test_choose_en2_prefers_exact_and_can_derive_compact_variant(self):
        self.assertEqual(
            MODULE.choose_en2_value(
                example_en="Registration",
                exact_diff_counter=MODULE.Counter({"Sign Up": 1}),
                manual_counter=MODULE.Counter({"Registered": 1}),
            ),
            "Sign Up",
        )
        self.assertEqual(
            MODULE.choose_en2_value(
                example_en="Level Up",
                exact_diff_counter=MODULE.Counter(),
                manual_counter=MODULE.Counter(
                    {
                        "Upgrade Module": 1,
                        "Upgrade Gold Mine": 1,
                        "Upgrade Defense Tower": 1,
                        "Upgrade Camp": 1,
                    }
                ),
            ),
            "Upgrade",
        )


class CliIntegrationTests(unittest.TestCase):
    def test_cli_generates_detail_and_final_workbooks(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample_language_table.xlsx"
            detail_path = temp_path / "detail.xlsx"
            final_path = temp_path / "final.xlsx"

            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Sheet0"
            worksheet.append(["ID", "cn", "en"])
            worksheet.append(["1", "报名", "Registration"])
            worksheet.append(["2", "报名条件", "Registration Requirements"])
            worksheet.append(["3", "报名倒计时", "Registration Countdown"])
            worksheet.append(["4", "报名", "Sign Up"])
            worksheet.append(["5", "升级", "Level Up"])
            worksheet.append(["6", "升级模块", "Upgrade Module"])
            worksheet.append(["7", "升级特权", "Upgrade Privilege"])
            worksheet.append(["8", "升级营地", "Upgrade Camp"])
            workbook.save(input_path)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    str(input_path),
                    "--output",
                    str(detail_path),
                    "--final-output",
                    str(final_path),
                    "--min-hit",
                    "1",
                    "--glossary-hit-threshold",
                    "1",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
            self.assertTrue(detail_path.exists())
            self.assertTrue(final_path.exists())

            final_workbook = load_workbook(final_path, read_only=True, data_only=True)
            glossary_sheet = final_workbook["Glossary"]
            rows = list(glossary_sheet.iter_rows(values_only=True))
            self.assertEqual(rows[0], ("ID", "CN", "EN", "EN2"))

            lookup = {row[1]: row for row in rows[1:]}
            self.assertEqual(lookup["报名"][2], "Registration")
            self.assertEqual(lookup["报名"][3], "Sign Up")
            self.assertEqual(lookup["升级"][2], "Level Up")
            self.assertEqual(lookup["升级"][3], "Upgrade")
            final_workbook.close()


if __name__ == "__main__":
    unittest.main()
