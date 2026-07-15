import frappe
from frappe import _
from frappe.model.document import Document


class EstateFlowSettings(Document):
    def validate(self):
        modes = (
            self.enable_landlord, self.enable_property_management, self.enable_housing_authority,
            self.enable_developer_sales, self.enable_brokerage, self.enable_hospitality,
            self.enable_community, self.enable_investment,
        )
        if not any(modes):
            frappe.throw(_("Enable at least one EstateFlow business mode."))
        if self.company:
            company = frappe.db.get_value("Company", self.company, ["default_currency", "country"], as_dict=True)
            self.default_currency = self.default_currency or company.default_currency
            self.country = self.country or company.country
        for fieldname in (
            "default_income_account", "service_charge_income_account", "accommodation_income_account",
            "security_deposit_account", "maintenance_expense_account", "commission_expense_account",
        ):
            account = self.get(fieldname)
            if not account:
                continue
            account_company = frappe.db.get_value("Account", account, "company")
            if account_company and account_company != self.company:
                frappe.throw(_("{0} must belong to the default company.").format(self.meta.get_label(fieldname)))
        if self.default_warehouse:
            warehouse_company = frappe.db.get_value("Warehouse", self.default_warehouse, "company")
            if warehouse_company and warehouse_company != self.company:
                frappe.throw(_("Default Warehouse must belong to the default company."))
