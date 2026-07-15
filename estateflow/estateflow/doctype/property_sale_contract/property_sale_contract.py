import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from estateflow.api.availability import get_conflicts
from estateflow.utils import get_estateflow_settings, get_property_defaults, release_space_if_unused, set_space_state


class PropertySaleContract(Document):
    def validate(self):
        self.contract_value = flt(self.sale_price) - flt(self.discount_amount)
        if self.contract_value <= 0:
            frappe.throw(_("Contract value must be greater than zero."))

        defaults = get_property_defaults(self.property)
        settings = get_estateflow_settings()
        self.company = self.company or defaults.company or settings.company
        self.currency = self.currency or defaults.currency or settings.default_currency

        total_installments = sum(flt(row.amount) for row in self.installments)
        if abs(total_installments - flt(self.contract_value)) > 0.01:
            frappe.throw(
                _("Payment plan total ({0}) must equal the contract value ({1}).").format(
                    frappe.format_value(total_installments, {"fieldtype": "Currency", "options": self.currency}),
                    frappe.format_value(self.contract_value, {"fieldtype": "Currency", "options": self.currency}),
                )
            )
        self._validate_percentages()

    def before_submit(self):
        self._assert_sale_available()
        self.status = "Active"

    def on_submit(self):
        if self.reservation and frappe.db.exists("Property Reservation", self.reservation):
            frappe.db.set_value("Property Reservation", self.reservation, "status", "Converted")
        has_tenant = frappe.db.exists(
            "Occupancy Agreement",
            {"space": self.space, "docstatus": 1, "status": ["in", ["Active", "Notice Given"]]},
        )
        if not has_tenant:
            set_space_state(self.space, "Under Contract", "", "")

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        release_space_if_unused(self.space)

    def _validate_percentages(self):
        percentages = [flt(row.percentage) for row in self.installments if row.percentage]
        if percentages and abs(sum(percentages) - 100) > 0.01:
            frappe.throw(_("Installment percentages must total 100%."))

    def _assert_sale_available(self):
        existing = frappe.db.exists(
            "Property Sale Contract",
            {
                "space": self.space,
                "docstatus": 1,
                "status": ["in", ["Active", "Completed", "Transferred"]],
                "name": ["!=", self.name],
            },
        )
        if existing:
            frappe.throw(_("This space already has Sale Contract {0}.").format(frappe.bold(existing)))

        # Reservations and non-tenanted occupation block the sale. A sale may
        # explicitly be made subject to an existing tenancy.
        start = min(row.due_date for row in self.installments)
        end = max(row.due_date for row in self.installments)
        if start == end:
            from frappe.utils import add_days
            end = add_days(end, 1)
        conflicts = get_conflicts(self.space, start, end)
        filtered = []
        for row in conflicts:
            if row.doctype == "Property Reservation" and row.name == self.reservation:
                continue
            if row.doctype == "Occupancy Agreement" and self.sale_subject_to_tenancy:
                continue
            filtered.append(row)
        if filtered:
            row = filtered[0]
            frappe.throw(_("The sale conflicts with {0} {1}.").format(row.doctype, frappe.bold(row.name)))

    @frappe.whitelist()
    def create_due_invoices(self, submit=None):
        self.check_permission("read")
        from estateflow.api.billing import generate_sale_installment_invoices

        return generate_sale_installment_invoices(self.name, submit=submit)

    @frappe.whitelist()
    def mark_completed(self):
        self.check_permission("write")
        if self.docstatus != 1:
            frappe.throw(_("Submit the sale contract first."))
        unpaid = [row for row in self.installments if row.status not in ("Paid", "Waived")]
        if unpaid:
            frappe.throw(_("All installments must be paid or waived before completion."))
        self.db_set("status", "Completed")
        set_space_state(self.space, "Sold", self.customer, "")
        return self.name
