import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from estateflow.api.availability import get_conflicts
from estateflow.utils import get_estateflow_settings, get_property_defaults, release_space_if_unused, set_space_state


class OccupancyAgreement(Document):
    def validate(self):
        if self.start_date and self.end_date and getdate(self.end_date) <= getdate(self.start_date):
            frappe.throw(_("Agreement end date must be after its start date."))
        if not self.charges:
            frappe.throw(_("Add at least one recurring charge."))
        for row in self.charges:
            if row.rate < 0:
                frappe.throw(_("Agreement charges cannot be negative."))

        space_property = frappe.db.get_value("Property Space", self.space, "property")
        if space_property and self.property != space_property:
            self.property = space_property
        defaults = get_property_defaults(self.property)
        settings = get_estateflow_settings()
        self.company = self.company or defaults.company or settings.company
        self.currency = self.currency or defaults.currency or settings.default_currency
        self.invoice_due_days = self.invoice_due_days or settings.default_receivable_days
        if not self.next_invoice_date and self.start_date:
            self.next_invoice_date = self.start_date

        if self.status in ("Active", "Notice Given") or self.docstatus == 1:
            self._assert_available()

    def before_submit(self):
        self._assert_available()
        self.status = "Active"

    def on_submit(self):
        if self.reservation and frappe.db.exists("Property Reservation", self.reservation):
            frappe.db.set_value("Property Reservation", self.reservation, "status", "Converted")
        set_space_state(self.space, "Occupied", self.customer, self.name)

    def on_cancel(self):
        self.db_set("status", "Terminated")
        release_space_if_unused(self.space)

    def _assert_available(self):
        conflicts = get_conflicts(
            self.space,
            self.start_date,
            self.end_date,
            "Occupancy Agreement",
            None if self.is_new() else self.name,
        )
        conflicts = [
            row for row in conflicts
            if not (row.doctype == "Property Reservation" and row.name == self.reservation)
        ]
        if conflicts:
            row = conflicts[0]
            frappe.throw(
                _("This agreement overlaps {0} {1} ({2} to {3}).").format(
                    row.doctype, frappe.bold(row.name), row.start_date, row.end_date
                )
            )

    @frappe.whitelist()
    def create_current_invoice(self, submit=None):
        self.check_permission("read")
        from estateflow.api.billing import generate_agreement_invoice

        invoice = generate_agreement_invoice(self.name, self.next_invoice_date, submit=submit)
        return invoice.name
