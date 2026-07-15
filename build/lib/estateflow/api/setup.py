"""One-screen EstateFlow onboarding.

The wizard deliberately creates only safe master data. It never creates ledger
accounts or tax rules silently; those remain explicit accounting decisions.
"""

import frappe
from frappe import _


MODE_FIELDS = {
    "landlord": "enable_landlord",
    "property_management": "enable_property_management",
    "housing_authority": "enable_housing_authority",
    "developer_sales": "enable_developer_sales",
    "brokerage": "enable_brokerage",
    "hospitality": "enable_hospitality",
    "community": "enable_community",
    "investment": "enable_investment",
}

DEFAULT_ITEMS = (
    ("ESTATEFLOW-RENT", "Property Rent", 1, 0),
    ("ESTATEFLOW-SERVICE-CHARGE", "Property Service Charge", 1, 0),
    ("ESTATEFLOW-ACCOMMODATION", "Accommodation", 1, 0),
    ("ESTATEFLOW-RESERVATION", "Reservation Charge", 1, 0),
    ("ESTATEFLOW-UTILITY", "Utility Rebilling", 1, 0),
    ("ESTATEFLOW-PROPERTY-SALE", "Property Sale Installment", 1, 0),
    ("ESTATEFLOW-MAINTENANCE", "Maintenance Service", 1, 1),
    ("ESTATEFLOW-COMMISSION", "Real Estate Commission", 0, 1),
)


@frappe.whitelist()
def get_setup_state():
    settings = frappe.get_single("EstateFlow Settings")
    companies = frappe.get_all("Company", fields=["name", "default_currency", "country"], order_by="is_group, name")
    return {
        "configured": bool(settings.company),
        "settings": settings.as_dict(),
        "companies": companies,
        "modes": MODE_FIELDS,
    }


@frappe.whitelist()
def complete_setup(company, business_modes=None, property_label="Property", create_standard_items=1,
                   create_initial_portfolio=1):
    if not frappe.has_permission("EstateFlow Settings", "write"):
        frappe.throw(_("You do not have permission to configure EstateFlow."), frappe.PermissionError)
    if not frappe.db.exists("Company", company):
        frappe.throw(_("Company {0} does not exist.").format(frappe.bold(company)))

    business_modes = frappe.parse_json(business_modes) if isinstance(business_modes, str) else business_modes
    business_modes = business_modes or ["landlord", "property_management"]
    company_defaults = frappe.db.get_value(
        "Company", company,
        ["default_currency", "country", "cost_center", "default_income_account", "default_expense_account"],
        as_dict=True,
    )

    settings = frappe.get_single("EstateFlow Settings")
    settings.company = company
    settings.country = company_defaults.country
    settings.default_currency = company_defaults.default_currency
    settings.default_cost_center = company_defaults.cost_center
    settings.default_income_account = company_defaults.default_income_account
    settings.maintenance_expense_account = company_defaults.default_expense_account
    settings.property_label = property_label or "Property"
    for fieldname in MODE_FIELDS.values():
        settings.set(fieldname, 0)
    for mode in business_modes:
        if mode in MODE_FIELDS:
            settings.set(MODE_FIELDS[mode], 1)
    settings.save()

    created_items = []
    if int(create_standard_items):
        created_items = create_default_items(company, company_defaults)

    portfolio = None
    if int(create_initial_portfolio):
        portfolio_name = f"{company} Property Portfolio"
        if not frappe.db.exists("Property Portfolio", portfolio_name):
            portfolio = frappe.get_doc(
                {
                    "doctype": "Property Portfolio",
                    "portfolio_name": portfolio_name,
                    "company": company,
                    "portfolio_type": _portfolio_type_for_modes(business_modes),
                    "status": "Active",
                }
            ).insert().name
        else:
            portfolio = portfolio_name

    frappe.clear_cache()
    return {
        "settings": settings.name,
        "portfolio": portfolio,
        "created_items": created_items,
        "route": "/app/estateflow-command-center",
    }


def create_default_items(company, company_defaults=None):
    company_defaults = company_defaults or frappe.db.get_value(
        "Company", company,
        ["default_income_account", "default_expense_account"],
        as_dict=True,
    )
    item_group = "EstateFlow Services"
    if not frappe.db.exists("Item Group", item_group):
        frappe.get_doc(
            {
                "doctype": "Item Group",
                "item_group_name": item_group,
                "parent_item_group": "All Item Groups",
                "is_group": 0,
            }
        ).insert(ignore_permissions=True)

    created = []
    for item_code, item_name, sales, purchase in DEFAULT_ITEMS:
        if frappe.db.exists("Item", item_code):
            continue
        item = frappe.get_doc(
            {
                "doctype": "Item",
                "item_code": item_code,
                "item_name": item_name,
                "item_group": item_group,
                "stock_uom": "Nos",
                "is_stock_item": 0,
                "is_sales_item": sales,
                "is_purchase_item": purchase,
                "include_item_in_manufacturing": 0,
                "item_defaults": [
                    {
                        "company": company,
                        "income_account": company_defaults.default_income_account if sales else None,
                        "expense_account": company_defaults.default_expense_account if purchase else None,
                    }
                ],
            }
        )
        item.insert(ignore_permissions=True)
        created.append(item.name)
    return created


def _portfolio_type_for_modes(modes):
    if "housing_authority" in modes:
        return "National Housing"
    if "hospitality" in modes:
        return "Hospitality Group"
    if "developer_sales" in modes:
        return "Development Portfolio"
    if "investment" in modes:
        return "Investment Fund"
    return "Private Holdings"
