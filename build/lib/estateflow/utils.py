from __future__ import annotations

import frappe
from frappe.utils import add_days, cint, get_datetime, now_datetime


def get_estateflow_settings():
    return frappe.get_cached_doc("EstateFlow Settings")


def get_property_defaults(property_name):
    if not property_name:
        return frappe._dict()
    return frappe.db.get_value(
        "Real Estate Property",
        property_name,
        ["company", "currency", "cost_center", "project", "warehouse", "income_account", "expense_account"],
        as_dict=True,
    ) or frappe._dict()


def set_space_state(space, occupancy_status=None, customer=None, agreement=None, housekeeping_status=None):
    values = {}
    if occupancy_status is not None:
        values["occupancy_status"] = occupancy_status
    if customer is not None:
        values["current_customer"] = customer
    if agreement is not None:
        values["current_agreement"] = agreement
    if housekeeping_status is not None:
        values["housekeeping_status"] = housekeeping_status
    if values:
        frappe.db.set_value("Property Space", space, values, update_modified=True)
    refresh_property_counts_for_space(space)


def release_space_if_unused(space):
    """Release a space only when no active agreement or checked-in booking remains."""
    active_agreement = frappe.db.exists(
        "Occupancy Agreement", {"space": space, "docstatus": 1, "status": ["in", ["Active", "Notice Given"]]}
    )
    checked_in = frappe.db.exists(
        "Property Reservation", {"space": space, "docstatus": 1, "status": "Checked In"}
    )
    active_sale = frappe.db.exists(
        "Property Sale Contract", {"space": space, "docstatus": 1, "status": ["in", ["Active", "Completed", "Transferred"]]}
    )
    if active_sale:
        return
    if active_agreement:
        agreement = frappe.db.get_value(
            "Occupancy Agreement", active_agreement, ["customer", "name"], as_dict=True
        )
        set_space_state(space, "Occupied", agreement.customer, agreement.name)
    elif checked_in:
        customer = frappe.db.get_value("Property Reservation", checked_in, "customer")
        set_space_state(space, "Occupied", customer, "")
    else:
        set_space_state(space, "Available", "", "")


def refresh_property_counts_for_space(space):
    property_name = frappe.db.get_value("Property Space", space, "property")
    if property_name:
        refresh_property_counts(property_name)


def refresh_property_counts(property_name):
    total = frappe.db.count("Property Space", {"property": property_name})
    available = frappe.db.count(
        "Property Space",
        {"property": property_name, "status": "Ready", "occupancy_status": "Available"},
    )
    frappe.db.set_value(
        "Real Estate Property",
        property_name,
        {"total_spaces": total, "available_spaces": available},
        update_modified=False,
    )


def calculate_sla_due(priority, reported_on=None):
    settings = get_estateflow_settings()
    base_hours = cint(settings.default_sla_hours or 24)
    multiplier = {"Emergency": 0.25, "High": 0.5, "Medium": 1, "Low": 2}.get(priority, 1)
    start = get_datetime(reported_on or now_datetime())
    return add_days(start, (base_hours * multiplier) / 24)
