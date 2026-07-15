import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt

from estateflow.utils import get_estateflow_settings, get_property_defaults


class RealEstateCommission(Document):
    def validate(self):
        if not (self.sales_partner or self.agent_supplier or self.agent_user):
            frappe.throw(_("Select a sales partner, agent supplier or internal agent."))
        if self.commission_rate:
            self.commission_amount = flt(self.basis_amount) * flt(self.commission_rate) / 100
        if flt(self.commission_amount) < 0:
            frappe.throw(_("Commission cannot be negative."))

    def before_submit(self):
        self.status = "Approved"

    @frappe.whitelist()
    def create_purchase_invoice(self, submit=None):
        self.check_permission("read")
        if self.docstatus != 1:
            frappe.throw(_("Submit and approve the commission first."))
        if not self.agent_supplier:
            frappe.throw(_("Select an Agent Supplier to create a payable invoice."))
        if self.purchase_invoice:
            return self.purchase_invoice
        item_code = "ESTATEFLOW-COMMISSION"
        if not frappe.db.exists("Item", item_code):
            frappe.throw(_("Run EstateFlow Setup to create the commission Item."))

        defaults = get_property_defaults(self.property)
        invoice = frappe.new_doc("Purchase Invoice")
        invoice.supplier = self.agent_supplier
        invoice.company = self.company
        invoice.currency = self.currency
        if invoice.meta.has_field("estateflow_property"):
            invoice.estateflow_property = self.property
            invoice.estateflow_space = self.space
        invoice.append(
            "items",
            {
                "item_code": item_code,
                "description": _("Commission for {0} {1}").format(self.reference_doctype, self.reference_name),
                "qty": 1,
                "rate": self.commission_amount,
                "expense_account": get_estateflow_settings().commission_expense_account or defaults.expense_account,
                "cost_center": defaults.cost_center,
            },
        )
        invoice.set_missing_values()
        invoice.insert()
        if str(submit) in ("1", "true", "True"):
            invoice.submit()
        self.db_set({"purchase_invoice": invoice.name, "status": "Payable"})
        return invoice.name
