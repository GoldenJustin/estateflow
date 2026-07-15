"""Installation and migration helpers for EstateFlow.

EstateFlow never patches ERPNext core. Integration fields are created with the
supported Custom Field API, making uninstall and upgrades predictable.
"""

import frappe
from frappe import _
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


ESTATEFLOW_ROLES = (
    ("EstateFlow Administrator", 1),
    ("Portfolio Manager", 1),
    ("Property Manager", 1),
    ("Leasing Officer", 1),
    ("Estate Agent", 1),
    ("Front Desk Officer", 1),
    ("Housing Officer", 1),
    ("Facilities Officer", 1),
    ("EstateFlow Portal User", 0),
)


def before_install():
    """Fail only when the ERPNext app is not installed on the target site.

    Checking for a Module Def named ``ERPNext`` is unreliable because ERPNext
    exposes domain modules rather than guaranteeing a module with that exact
    name. The installed-app registry is the supported dependency check and is
    also what Frappe uses for ``required_apps``.
    """
    if "erpnext" not in set(frappe.get_installed_apps()):
        frappe.throw(_("EstateFlow requires ERPNext to be installed first."))


def after_install():
    ensure_roles()
    create_estateflow_custom_fields()
    frappe.clear_cache()


def after_migrate():
    ensure_roles()
    create_estateflow_custom_fields()


def ensure_roles():
    for role_name, desk_access in ESTATEFLOW_ROLES:
        if frappe.db.exists("Role", role_name):
            continue
        role = frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": desk_access,
                "is_custom": 1,
            }
        )
        role.insert(ignore_permissions=True)


def _link(label, fieldname, options, insert_after, **extra):
    value = {
        "label": label,
        "fieldname": fieldname,
        "fieldtype": "Link",
        "options": options,
        "insert_after": insert_after,
        "translatable": 0,
    }
    value.update(extra)
    return value


def get_custom_fields():
    property_field = lambda after="estateflow_section": _link(
        "EstateFlow Property", "estateflow_property", "Real Estate Property", after
    )
    space_field = lambda after="estateflow_property": _link(
        "EstateFlow Unit / Room / Space", "estateflow_space", "Property Space", after
    )

    return {
        "Sales Invoice": [
            {
                "label": "EstateFlow",
                "fieldname": "estateflow_section",
                "fieldtype": "Section Break",
                "insert_after": "customer",
                "collapsible": 1,
            },
            property_field(),
            space_field(),
            _link("Occupancy Agreement", "estateflow_agreement", "Occupancy Agreement", "estateflow_space"),
            _link("Reservation / Booking", "estateflow_reservation", "Property Reservation", "estateflow_agreement"),
            _link("Property Sale Contract", "estateflow_sale_contract", "Property Sale Contract", "estateflow_reservation"),
            {
                "label": "Billing Period Start",
                "fieldname": "estateflow_billing_period_start",
                "fieldtype": "Date",
                "insert_after": "estateflow_sale_contract",
            },
            {
                "label": "Billing Period End",
                "fieldname": "estateflow_billing_period_end",
                "fieldtype": "Date",
                "insert_after": "estateflow_billing_period_start",
            },
        ],
        "Purchase Invoice": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "supplier", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Property Work Order", "estateflow_work_order", "Property Work Order", "estateflow_space"),
        ],
        "Payment Entry": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "party", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Occupancy Agreement", "estateflow_agreement", "Occupancy Agreement", "estateflow_space"),
            _link("Reservation / Booking", "estateflow_reservation", "Property Reservation", "estateflow_agreement"),
        ],
        "Material Request": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "schedule_date", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Property Work Order", "estateflow_work_order", "Property Work Order", "estateflow_space"),
        ],
        "Purchase Order": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "supplier", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Property Work Order", "estateflow_work_order", "Property Work Order", "estateflow_space"),
        ],
        "Purchase Receipt": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "supplier", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Property Work Order", "estateflow_work_order", "Property Work Order", "estateflow_space"),
        ],
        "Stock Entry": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "stock_entry_type", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Property Work Order", "estateflow_work_order", "Property Work Order", "estateflow_space"),
        ],
        "Journal Entry": [
            {"label": "EstateFlow", "fieldname": "estateflow_section", "fieldtype": "Section Break", "insert_after": "voucher_type", "collapsible": 1},
            property_field(),
            space_field(),
            _link("Occupancy Agreement", "estateflow_agreement", "Occupancy Agreement", "estateflow_space"),
        ],
    }


def create_estateflow_custom_fields():
    create_custom_fields(get_custom_fields(), update=True)
