"""Shared availability rules for leases, bookings, sales holds and allocations."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import getdate


BLOCKING_RESERVATION_STATUSES = ("Tentative", "Confirmed", "Checked In")
BLOCKING_AGREEMENT_STATUSES = ("Active", "Notice Given")


def _normalise_dates(start_date, end_date):
    start = getdate(start_date)
    end = getdate(end_date)
    if end <= start:
        frappe.throw(_("End or departure date must be after the start or arrival date."))
    return start, end


def get_conflicts(space, start_date, end_date, exclude_doctype=None, exclude_name=None):
    """Return blocking reservations and occupancy agreements.

    Date intervals are treated as half-open: a guest may arrive on the date the
    previous guest departs. This same rule keeps renewals and unit transfers
    deterministic.
    """
    start, end = _normalise_dates(start_date, end_date)
    conflicts = []

    reservation_params = {
        "space": space,
        "start": start,
        "end": end,
        "exclude_name": exclude_name or "",
    }
    reservation_sql = """
        select name, status, arrival_date as start_date, departure_date as end_date
        from `tabProperty Reservation`
        where space = %(space)s
          and docstatus < 2
          and status in ('Tentative', 'Confirmed', 'Checked In')
          and arrival_date < %(end)s
          and departure_date > %(start)s
    """
    if exclude_doctype == "Property Reservation" and exclude_name:
        reservation_sql += " and name != %(exclude_name)s"
    for row in frappe.db.sql(reservation_sql, reservation_params, as_dict=True):
        row["doctype"] = "Property Reservation"
        conflicts.append(row)

    agreement_params = {
        "space": space,
        "start": start,
        "end": end,
        "exclude_name": exclude_name or "",
    }
    agreement_sql = """
        select name, status, start_date, end_date
        from `tabOccupancy Agreement`
        where space = %(space)s
          and docstatus = 1
          and status in ('Active', 'Notice Given')
          and start_date < %(end)s
          and end_date > %(start)s
    """
    if exclude_doctype == "Occupancy Agreement" and exclude_name:
        agreement_sql += " and name != %(exclude_name)s"
    for row in frappe.db.sql(agreement_sql, agreement_params, as_dict=True):
        row["doctype"] = "Occupancy Agreement"
        conflicts.append(row)

    return conflicts


def assert_space_available(space, start_date, end_date, exclude_doctype=None, exclude_name=None):
    if not frappe.db.exists("Property Space", space):
        frappe.throw(_("Property Space {0} does not exist.").format(frappe.bold(space)))

    state = frappe.db.get_value("Property Space", space, ["status", "occupancy_status"], as_dict=True)
    if state.status in ("Under Construction", "Out of Service", "Inactive"):
        frappe.throw(_("{0} is not operational.").format(frappe.bold(space)))
    if state.occupancy_status in ("Sold", "Owner Occupied", "Blocked"):
        frappe.throw(_("{0} is currently {1}.").format(frappe.bold(space), state.occupancy_status))

    conflicts = get_conflicts(space, start_date, end_date, exclude_doctype, exclude_name)
    if conflicts:
        conflict = conflicts[0]
        frappe.throw(
            _("{0} is unavailable because it overlaps {1} {2} ({3} to {4}).").format(
                frappe.bold(space), conflict.doctype, frappe.bold(conflict.name),
                conflict.start_date, conflict.end_date
            )
        )
    return True


@frappe.whitelist()
def get_available_spaces(property=None, start_date=None, end_date=None, use="Stay", space_type=None):
    if not start_date or not end_date:
        frappe.throw(_("Start and end dates are required."))
    start, end = _normalise_dates(start_date, end_date)

    filters = {"status": "Ready"}
    if property:
        filters["property"] = property
    if space_type:
        filters["space_type"] = space_type

    use_field = {
        "Stay": "bookable",
        "Rent": "rentable",
        "Sale": "sellable",
        "Housing": "allocatable",
    }.get(use, "bookable")
    filters[use_field] = 1

    spaces = frappe.get_all(
        "Property Space",
        filters=filters,
        fields=[
            "name", "space_name", "property", "space_type", "occupancy_status",
            "currency", "nightly_rate", "base_rent", "sale_price", "max_adults",
            "max_children", "housekeeping_status",
        ],
        order_by="property, space_name",
        limit_page_length=500,
    )
    available = []
    for space in spaces:
        if space.occupancy_status in ("Sold", "Owner Occupied", "Blocked"):
            continue
        if not get_conflicts(space.name, start, end):
            available.append(space)
    return available
