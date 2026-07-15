"""Static checks that run without importing Frappe."""

import ast
import json
import unittest
from pathlib import Path


PACKAGE = Path(__file__).resolve().parents[1]
MODULE = PACKAGE / "estateflow"
DOCTYPE_ROOT = MODULE / "doctype"


class TestEstateFlowStaticSchema(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doctypes = {}
        for path in DOCTYPE_ROOT.glob("*/*.json"):
            data = json.loads(path.read_text())
            cls.doctypes[data["name"]] = (path, data)

    def test_expected_doctype_count(self):
        self.assertEqual(len(self.doctypes), 26)

    def test_field_order_is_complete_and_unique(self):
        for name, (path, data) in self.doctypes.items():
            with self.subTest(doctype=name):
                order = data.get("field_order", [])
                fields = [field["fieldname"] for field in data.get("fields", [])]
                self.assertEqual(len(order), len(set(order)), f"duplicate field_order entry in {path}")
                self.assertEqual(len(fields), len(set(fields)), f"duplicate field in {path}")
                self.assertEqual(set(order), set(fields), f"field_order mismatch in {path}")

    def test_child_table_options_exist(self):
        custom_names = set(self.doctypes)
        for name, (_, data) in self.doctypes.items():
            for field in data.get("fields", []):
                if field.get("fieldtype") == "Table":
                    with self.subTest(doctype=name, field=field["fieldname"]):
                        self.assertIn(field.get("options"), custom_names)
                        target = self.doctypes[field["options"]][1]
                        self.assertEqual(target.get("istable"), 1)

    def test_custom_link_targets_exist(self):
        custom_names = set(self.doctypes)
        for name, (_, data) in self.doctypes.items():
            for field in data.get("fields", []):
                if field.get("fieldtype") == "Link" and field.get("options") in custom_names:
                    self.assertIn(field["options"], custom_names, f"{name}.{field['fieldname']}")

    def test_json_documents_are_well_formed(self):
        json_files = list(PACKAGE.rglob("*.json"))
        self.assertGreater(len(json_files), 25)
        for path in json_files:
            with self.subTest(path=path):
                json.loads(path.read_text())

    def test_python_files_parse(self):
        for path in PACKAGE.rglob("*.py"):
            with self.subTest(path=path):
                ast.parse(path.read_text(), filename=str(path))

    def test_core_transactions_are_submittable(self):
        expected = {
            "Property Offer", "Property Reservation", "Occupancy Agreement",
            "Property Sale Contract", "Property Work Order", "Property Inspection",
            "Utility Reading", "Property Allocation", "Real Estate Commission",
            "Security Deposit Transaction",
        }
        actual = {name for name, (_, data) in self.doctypes.items() if data.get("is_submittable")}
        self.assertEqual(actual, expected)

    def test_settings_is_single(self):
        self.assertEqual(self.doctypes["EstateFlow Settings"][1].get("issingle"), 1)

    def test_command_center_styles_are_shipped_and_explicitly_loaded(self):
        stylesheet = PACKAGE / "public" / "css" / "estateflow.css"
        guide_stylesheet = PACKAGE / "public" / "css" / "estateflow-guide.css"
        page_script = MODULE / "page" / "estateflow_command_center" / "estateflow_command_center.js"
        guide_script = MODULE / "page" / "estateflow_guide" / "estateflow_guide.js"
        hooks = (PACKAGE / "hooks.py").read_text()
        self.assertTrue(stylesheet.is_file())
        self.assertTrue(guide_stylesheet.is_file())
        self.assertGreater(stylesheet.stat().st_size, 1000)
        self.assertGreater(guide_stylesheet.stat().st_size, 1000)
        self.assertIn("/assets/estateflow/css/estateflow.css", page_script.read_text())
        self.assertIn("/assets/estateflow/css/estateflow-guide.css", guide_script.read_text())
        self.assertIn("/assets/estateflow/css/estateflow.css", hooks)
        self.assertIn("/assets/estateflow/css/estateflow-guide.css", hooks)

    def test_in_app_guide_is_standard_page(self):
        path = MODULE / "page" / "estateflow_guide" / "estateflow_guide.json"
        page = json.loads(path.read_text())
        self.assertEqual(page["name"], "estateflow-guide")
        self.assertEqual(page["standard"], "Yes")
        self.assertTrue((PACKAGE / "api" / "guide.py").is_file())


if __name__ == "__main__":
    unittest.main()
