import frappe
from frappe import _
from frappe.model.document import Document


class PropertyPortfolio(Document):
    def validate(self):
        if self.company:
            company = frappe.db.get_value("Company", self.company, ["default_currency", "cost_center"], as_dict=True)
            self.currency = self.currency or company.default_currency
            self.portfolio_cost_center = self.portfolio_cost_center or company.cost_center
        if self.portfolio_cost_center:
            cc_company = frappe.db.get_value("Cost Center", self.portfolio_cost_center, "company")
            if cc_company and cc_company != self.company:
                frappe.throw(_("Portfolio Cost Center must belong to the portfolio company."))
