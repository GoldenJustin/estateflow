import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, flt, getdate, now_datetime, nowdate

from estateflow.api.availability import get_conflicts
from estateflow.utils import get_estateflow_settings, get_property_defaults, release_space_if_unused, set_space_state


class OccupancyAgreement(Document):
    def validate(self):
        if self.start_date and self.end_date and getdate(self.end_date) <= getdate(self.start_date):
            frappe.throw(_("Agreement end date must be after its start date."))
        if not self.charges and not self.payment_milestones:
            frappe.throw(_("Add at least one recurring charge or payment milestone."))
        for row in self.charges:
            if flt(row.rate) < 0:
                frappe.throw(_("Agreement charges cannot be negative."))
        for row in self.payment_milestones:
            if flt(row.amount) <= 0:
                frappe.throw(_("Milestone amounts must be greater than zero."))
            if getdate(row.due_date) < getdate(self.start_date):
                frappe.throw(_("Milestone {0} cannot be due before the agreement starts.").format(row.milestone))

        space_property = frappe.db.get_value("Property Space", self.space, "property")
        if space_property and self.property != space_property:
            self.property = space_property
        defaults = get_property_defaults(self.property)
        settings = get_estateflow_settings()
        self.company = self.company or defaults.company or settings.company
        self.currency = self.currency or defaults.currency or settings.default_currency
        self.invoice_due_days = self.invoice_due_days or settings.default_receivable_days
        self.billing_start_policy = self.billing_start_policy or settings.default_billing_start_policy or "On Activation"
        if self.billing_start_policy == "Days Before Period Start":
            self.invoice_lead_days = self.invoice_lead_days or settings.default_invoice_lead_days
        else:
            self.invoice_lead_days = 0
        if not self.next_invoice_date and self.start_date and self.charges:
            self.next_invoice_date = self.start_date

        if self.status in ("Active", "Notice Given", "Pending Activation") or self.docstatus == 1:
            self._assert_available()

    def before_submit(self):
        self._assert_available()
        self.status = "Active" if getdate(self.start_date) <= getdate(nowdate()) else "Pending Activation"

    def on_submit(self):
        if self.reservation and frappe.db.exists("Property Reservation", self.reservation):
            frappe.db.set_value("Property Reservation", self.reservation, "status", "Converted")
        if self.status == "Active":
            self._activate_side_effects()
        else:
            set_space_state(self.space, "Reserved", "", "")
        self._generate_automatic_invoices(on_activation=self.status == "Active")

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

    def _activate_side_effects(self):
        self.db_set({"status": "Active", "activation_date": now_datetime()})
        set_space_state(self.space, "Occupied", self.customer, self.name)
        from estateflow.api.notifications import notify_contract_activation
        notify_contract_activation(self)

    def _generate_automatic_invoices(self, on_activation=False):
        if not self.auto_generate_invoices:
            return
        settings = get_estateflow_settings()
        from estateflow.api.billing import generate_agreement_invoice, generate_agreement_milestone_invoices

        lead_trigger_reached = (
            self.billing_start_policy == "Days Before Period Start"
            and self.next_invoice_date
            and getdate(nowdate()) >= getdate(add_days(self.next_invoice_date, -(self.invoice_lead_days or 0)))
        )
        period_start_reached = (
            self.billing_start_policy == "On Period Start"
            and self.next_invoice_date
            and getdate(nowdate()) >= getdate(self.next_invoice_date)
        )
        if self.charges and (
            (on_activation and settings.generate_first_invoice_on_activation and self.billing_start_policy == "On Activation")
            or period_start_reached
            or lead_trigger_reached
        ):
            generate_agreement_invoice(self.name, self.next_invoice_date)
        generate_agreement_milestone_invoices(self.name)

    @frappe.whitelist()
    def activate_contract(self):
        self.check_permission("write")
        if self.docstatus != 1:
            frappe.throw(_("Submit the agreement before activation."))
        if self.status == "Active":
            return self.name
        if self.status not in ("Pending Activation", "Draft"):
            frappe.throw(_("Only a pending agreement can be activated."))
        self._assert_available()
        self._activate_side_effects()
        self._generate_automatic_invoices(on_activation=True)
        return self.name

    @frappe.whitelist()
    def expire_contract(self):
        self.check_permission("write")
        if self.docstatus != 1 or self.status not in ("Active", "Notice Given", "Pending Activation"):
            frappe.throw(_("Only a current submitted agreement can be expired."))
        self.db_set("status", "Expired")
        release_space_if_unused(self.space)
        from estateflow.api.notifications import notify_contract_expired
        notify_contract_expired(self)
        return self.name

    @frappe.whitelist()
    def create_current_invoice(self, submit=None):
        self.check_permission("read")
        from estateflow.api.billing import generate_agreement_invoice
        invoice = generate_agreement_invoice(self.name, self.next_invoice_date, submit=submit)
        return invoice.name

    @frappe.whitelist()
    def create_due_invoices(self, submit=None):
        self.check_permission("read")
        from estateflow.api.billing import generate_due_agreement_invoices_for_contract
        return generate_due_agreement_invoices_for_contract(self.name, submit=submit)
