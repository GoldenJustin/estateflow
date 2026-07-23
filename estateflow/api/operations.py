"""Scheduled contract, reservation and listing state transitions."""

import frappe
from frappe.utils import getdate, now_datetime, nowdate

from estateflow.utils import get_estateflow_settings, release_space_if_unused


@frappe.whitelist()
def run_daily_operations():
    if frappe.request:
        frappe.only_for(("System Manager", "EstateFlow Administrator"))
    settings = get_estateflow_settings()
    now = now_datetime()
    today = getdate(nowdate())

    expired_holds = frappe.get_all(
        "Property Reservation",
        filters={
            "docstatus": ["<", 2],
            "status": ["in", ["Draft", "Tentative"]],
            "hold_expires_on": ["<", now],
        },
        fields=["name", "space"],
        limit_page_length=1000,
    )
    for row in expired_holds:
        frappe.db.set_value("Property Reservation", row.name, "status", "Expired")
        release_space_if_unused(row.space)

    if settings.auto_activate_contracts:
        pending = frappe.get_all(
            "Occupancy Agreement",
            filters={"docstatus": 1, "status": "Pending Activation", "start_date": ["<=", today], "end_date": [">=", today]},
            pluck="name",
            limit_page_length=1000,
        )
        for name in pending:
            try:
                frappe.get_doc("Occupancy Agreement", name).activate_contract()
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"EstateFlow contract activation: {name}")

    if settings.auto_expire_contracts:
        ended = frappe.get_all(
            "Occupancy Agreement",
            filters={
                "docstatus": 1,
                "status": ["in", ["Pending Activation", "Active", "Notice Given"]],
                "end_date": ["<", today],
            },
            pluck="name",
            limit_page_length=1000,
        )
        for name in ended:
            try:
                frappe.get_doc("Occupancy Agreement", name).expire_contract()
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"EstateFlow contract expiry: {name}")

    for name in frappe.get_all(
        "Property Listing",
        filters={"status": "Active", "valid_until": ["<", today]},
        pluck="name",
        limit_page_length=1000,
    ):
        frappe.db.set_value("Property Listing", name, "status", "Expired", update_modified=False)

    for name in frappe.get_all(
        "Property Offer",
        filters={
            "status": ["not in", ["Accepted", "Rejected", "Withdrawn", "Expired"]],
            "valid_until": ["<", today],
        },
        pluck="name",
        limit_page_length=1000,
    ):
        frappe.db.set_value("Property Offer", name, "status", "Expired", update_modified=False)
