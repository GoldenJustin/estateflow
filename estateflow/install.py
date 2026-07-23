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
    apply_v020_defaults()


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
            {
                "label": "Billing Source",
                "fieldname": "estateflow_billing_source",
                "fieldtype": "Select",
                "options": "Recurring Charge\nAgreement Milestone\nReservation / Stay\nProperty Sale Milestone\nUtility Reading\nManual Invoice",
                "insert_after": "estateflow_billing_period_end",
            },
            {
                "label": "Milestone Row",
                "fieldname": "estateflow_milestone_row",
                "fieldtype": "Data",
                "insert_after": "estateflow_billing_source",
                "read_only": 1,
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


def apply_v020_defaults():
    """Enable new v0.2 automation safely once for already-configured sites."""
    settings = frappe.get_single("EstateFlow Settings")
    if not settings.company or settings.configuration_version == "0.2.0":
        return
    from estateflow.api.setup import TEMPLATE_FIELDS, create_default_email_templates

    create_default_email_templates()
    defaults = {
        "auto_activate_contracts": 1,
        "auto_expire_contracts": 1,
        "generate_first_invoice_on_activation": 1,
        "default_billing_start_policy": "On Activation",
        "default_invoice_lead_days": 0,
        "contract_expiry_reminder_days": "90,60,30,14,7,1",
        "overdue_reminder_days": "1,7,14,30",
        "send_contract_activation_email": 1,
        "send_contract_expiry_alerts": 1,
        "send_contract_expired_email": 1,
        "send_invoice_email": 1,
        "send_payment_receipt_email": 1,
        "send_overdue_reminders": 1,
        "send_reservation_confirmation_email": 1,
    }
    for fieldname, value in defaults.items():
        settings.set(fieldname, value)
    for fieldname, template_name in TEMPLATE_FIELDS.items():
        settings.set(fieldname, settings.get(fieldname) or template_name)
    settings.configuration_version = "0.2.0"
    settings.save(ignore_permissions=True)
    frappe.db.sql(
        """
        update `tabOccupancy Agreement`
        set auto_generate_invoices = 1,
            billing_start_policy = coalesce(nullif(billing_start_policy, ''), 'On Activation'),
            invoice_lead_days = coalesce(invoice_lead_days, 0)
        where docstatus < 2
        """
    )
    frappe.clear_cache(doctype="EstateFlow Settings")
