import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate

from estateflow import __version__
from estateflow.api.uat import get_cases


class EstateFlowUATRun(Document):
    def before_insert(self):
        self.app_version = __version__
        self.test_date = self.test_date or nowdate()
        if not self.results and self.business_case:
            self._load_cases()

    def validate(self):
        if not self.results and self.business_case:
            self._load_cases()
        self.app_version = __version__
        self._calculate_summary()
        if self.status == "Signed Off" and not self.client_signoff_name:
            frappe.throw(_("Client Sign-off Name is required before sign-off."))

    def before_submit(self):
        self._calculate_summary()
        untested = [row for row in self.results if row.status in ("Not Tested", "Blocked")]
        if untested:
            frappe.throw(_("Complete or mark Not Applicable all test cases before submitting the UAT run."))
        self.status = "Failed" if self.failed_tests else "Passed"

    def _load_cases(self):
        self.set("results", [])
        for row in get_cases(self.business_case):
            self.append("results", row)
        self._calculate_summary()

    def _calculate_summary(self):
        self.total_tests = len(self.results)
        self.passed_tests = sum(1 for row in self.results if row.status == "Pass")
        self.failed_tests = sum(1 for row in self.results if row.status == "Fail")
        self.blocked_tests = sum(1 for row in self.results if row.status == "Blocked")
        completed = sum(1 for row in self.results if row.status not in ("Not Tested", "Blocked"))
        self.completion_percentage = (completed / self.total_tests * 100) if self.total_tests else 0
        if self.docstatus == 0 and self.status == "Planned" and completed:
            self.status = "In Progress"

    @frappe.whitelist()
    def reload_template(self):
        self.check_permission("write")
        self._load_cases()
        self.save()
        return len(self.results)
