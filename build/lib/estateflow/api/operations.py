"""Scheduled state transitions and operational helper endpoints."""

import frappe
from frappe.utils import getdate, now_datetime, nowdate

from estateflow.utils import release_space_if_unused


def run_daily_operations():
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

    ended_agreements = frappe.get_all(
        "Occupancy Agreement",
        filters={"docstatus": 1, "status": ["in", ["Active", "Notice Given"]], "end_date": ["<", today]},
        fields=["name", "space"],
        limit_page_length=1000,
    )
    for row in ended_agreements:
        frappe.db.set_value("Occupancy Agreement", row.name, "status", "Expired")
        release_space_if_unused(row.space)

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
