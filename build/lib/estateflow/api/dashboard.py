"""Fast, permission-aware aggregates for the EstateFlow Command Center."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, flt, getdate, nowdate

from estateflow.utils import get_estateflow_settings


def _scalar(query, values=None):
    result = frappe.db.sql(query, values or {}, as_dict=False)
    return result[0][0] if result and result[0] else 0


def _property_condition(alias, company=None, property_name=None, params=None):
    params = params if params is not None else {}
    conditions = []
    if company:
        conditions.append(f"{alias}.company = %(company)s")
        params["company"] = company
    if property_name:
        conditions.append(f"{alias}.name = %(property)s")
        params["property"] = property_name
    return (" and " + " and ".join(conditions)) if conditions else ""


@frappe.whitelist()
def get_command_center(company=None, property=None, from_date=None, to_date=None):
    if not frappe.has_permission("Real Estate Property", "read"):
        frappe.throw(_("You do not have permission to view EstateFlow."), frappe.PermissionError)

    settings = get_estateflow_settings()
    company = company or settings.company
    from_date = getdate(from_date or add_days(nowdate(), -30))
    to_date = getdate(to_date or nowdate())
    params = {"company": company, "property": property, "from_date": from_date, "to_date": to_date, "today": nowdate()}

    pcond = ""
    if company:
        pcond += " and p.company = %(company)s"
    if property:
        pcond += " and p.name = %(property)s"

    properties = _scalar(f"select count(*) from `tabReal Estate Property` p where p.status != 'Disposed' {pcond}", params)
    spaces = frappe.db.sql(
        f"""
        select s.occupancy_status, count(*) as total
        from `tabProperty Space` s
        inner join `tabReal Estate Property` p on p.name = s.property
        where s.status != 'Inactive' {pcond}
        group by s.occupancy_status
        """,
        params,
        as_dict=True,
    )
    space_counts = {row.occupancy_status: row.total for row in spaces}
    total_spaces = sum(space_counts.values())
    available = space_counts.get("Available", 0)
    occupied = space_counts.get("Occupied", 0) + space_counts.get("Owner Occupied", 0)
    rentable_base = max(0, total_spaces - space_counts.get("Sold", 0))
    occupancy_rate = (occupied / rentable_base * 100) if rentable_base else 0

    invoice_property_filter = ""
    if property:
        invoice_property_filter = " and si.estateflow_property = %(property)s"
    billed = _scalar(
        f"""
        select coalesce(sum(si.grand_total), 0)
        from `tabSales Invoice` si
        where si.docstatus = 1 and si.company = %(company)s
          and si.posting_date between %(from_date)s and %(to_date)s
          and coalesce(si.estateflow_property, '') != '' {invoice_property_filter}
        """,
        params,
    ) if company else 0
    collected = _scalar(
        f"""
        select coalesce(sum(si.grand_total - si.outstanding_amount), 0)
        from `tabSales Invoice` si
        where si.docstatus = 1 and si.company = %(company)s
          and si.posting_date between %(from_date)s and %(to_date)s
          and coalesce(si.estateflow_property, '') != '' {invoice_property_filter}
        """,
        params,
    ) if company else 0
    arrears = _scalar(
        f"""
        select coalesce(sum(si.outstanding_amount), 0)
        from `tabSales Invoice` si
        where si.docstatus = 1 and si.company = %(company)s
          and si.due_date < %(today)s and si.outstanding_amount > 0
          and coalesce(si.estateflow_property, '') != '' {invoice_property_filter}
        """,
        params,
    ) if company else 0

    lease_property_filter = " and a.property = %(property)s" if property else ""
    leases_expiring = _scalar(
        f"""
        select count(*) from `tabOccupancy Agreement` a
        inner join `tabReal Estate Property` p on p.name = a.property
        where a.docstatus = 1 and a.status in ('Active', 'Notice Given')
          and a.end_date between %(today)s and date_add(%(today)s, interval 90 day)
          {pcond} {lease_property_filter}
        """.replace(" and a.property = %(property)s and a.property = %(property)s", " and a.property = %(property)s"),
        params,
    )

    maintenance_filter = " and mr.property = %(property)s" if property else ""
    open_maintenance = _scalar(
        f"""
        select count(*) from `tabMaintenance Request` mr
        inner join `tabReal Estate Property` p on p.name = mr.property
        where mr.status not in ('Resolved', 'Closed', 'Cancelled') {pcond} {maintenance_filter}
        """.replace(" and mr.property = %(property)s and mr.property = %(property)s", " and mr.property = %(property)s"),
        params,
    )
    overdue_maintenance = _scalar(
        f"""
        select count(*) from `tabMaintenance Request` mr
        inner join `tabReal Estate Property` p on p.name = mr.property
        where mr.status not in ('Resolved', 'Closed', 'Cancelled')
          and mr.sla_due_on < now() {pcond} {maintenance_filter}
        """.replace(" and mr.property = %(property)s and mr.property = %(property)s", " and mr.property = %(property)s"),
        params,
    )

    reservation_filter = " and r.property = %(property)s" if property else ""
    arrivals_today = _scalar(
        f"""
        select count(*) from `tabProperty Reservation` r
        inner join `tabReal Estate Property` p on p.name = r.property
        where r.docstatus = 1 and r.status = 'Confirmed' and r.arrival_date = %(today)s
          {pcond} {reservation_filter}
        """.replace(" and r.property = %(property)s and r.property = %(property)s", " and r.property = %(property)s"),
        params,
    )
    active_sales = _scalar(
        f"""
        select count(*) from `tabProperty Sale Contract` c
        inner join `tabReal Estate Property` p on p.name = c.property
        where c.docstatus = 1 and c.status = 'Active' {pcond}
        """,
        params,
    )

    collection_rate = (flt(collected) / flt(billed) * 100) if billed else 0
    cards = [
        {"key": "properties", "label": _("Properties"), "value": properties, "format": "number", "tone": "indigo", "route": "List/Real Estate Property"},
        {"key": "spaces", "label": _("Units / Rooms / Spaces"), "value": total_spaces, "format": "number", "tone": "slate", "route": "List/Property Space"},
        {"key": "occupancy", "label": _("Occupancy"), "value": occupancy_rate, "format": "percent", "tone": "emerald", "route": "query-report/Availability Register"},
        {"key": "available", "label": _("Available Now"), "value": available, "format": "number", "tone": "cyan", "route": "List/Property Space/List"},
        {"key": "billed", "label": _("Billed"), "value": billed, "format": "currency", "tone": "violet", "route": "List/Sales Invoice"},
        {"key": "collection", "label": _("Collection Rate"), "value": collection_rate, "format": "percent", "tone": "emerald", "route": "List/Payment Entry"},
        {"key": "arrears", "label": _("Overdue Receivables"), "value": arrears, "format": "currency", "tone": "rose", "route": "query-report/Accounts Receivable"},
        {"key": "maintenance", "label": _("Open Maintenance"), "value": open_maintenance, "format": "number", "tone": "amber", "subtext": _("{0} beyond SLA").format(overdue_maintenance), "route": "List/Maintenance Request"},
    ]

    upcoming = _get_upcoming(params, pcond)
    activity = [
        {"label": _("Arrivals today"), "value": arrivals_today, "icon": "log-in", "route": "List/Property Reservation"},
        {"label": _("Leases expiring in 90 days"), "value": leases_expiring, "icon": "calendar", "route": "query-report/Lease Expiry"},
        {"label": _("Active property sales"), "value": active_sales, "icon": "trending-up", "route": "List/Property Sale Contract"},
        {"label": _("Maintenance beyond SLA"), "value": overdue_maintenance, "icon": "alert-triangle", "route": "List/Maintenance Request"},
    ]

    return {
        "cards": cards,
        "space_status": [{"label": key, "value": value} for key, value in space_counts.items()],
        "activity": activity,
        "upcoming": upcoming,
        "currency": settings.default_currency,
        "filters": {"company": company, "property": property, "from_date": from_date, "to_date": to_date},
        "business_modes": [
            key for key, fieldname in {
                "landlord": "enable_landlord",
                "property_management": "enable_property_management",
                "housing_authority": "enable_housing_authority",
                "developer_sales": "enable_developer_sales",
                "brokerage": "enable_brokerage",
                "hospitality": "enable_hospitality",
                "community": "enable_community",
                "investment": "enable_investment",
            }.items() if settings.get(fieldname)
        ],
        "generated_at": frappe.utils.now_datetime(),
    }


def _get_upcoming(params, property_condition):
    rows = []
    property_filter = " and a.property = %(property)s" if params.get("property") else ""
    agreements = frappe.db.sql(
        f"""
        select a.name, a.customer, a.property, a.space, a.end_date
        from `tabOccupancy Agreement` a
        inner join `tabReal Estate Property` p on p.name = a.property
        where a.docstatus = 1 and a.status in ('Active', 'Notice Given')
          and a.end_date >= %(today)s {property_condition} {property_filter}
        order by a.end_date asc limit 6
        """.replace(" and a.property = %(property)s and a.property = %(property)s", " and a.property = %(property)s"),
        params,
        as_dict=True,
    )
    for row in agreements:
        rows.append({
            "type": _("Lease expiry"), "title": row.customer, "meta": f"{row.property} · {row.space}",
            "date": row.end_date, "doctype": "Occupancy Agreement", "name": row.name,
        })

    reservation_filter = " and r.property = %(property)s" if params.get("property") else ""
    reservations = frappe.db.sql(
        f"""
        select r.name, r.customer, r.guest_name, r.property, r.space, r.arrival_date
        from `tabProperty Reservation` r
        inner join `tabReal Estate Property` p on p.name = r.property
        where r.docstatus = 1 and r.status = 'Confirmed' and r.arrival_date >= %(today)s
          {property_condition} {reservation_filter}
        order by r.arrival_date asc limit 6
        """.replace(" and r.property = %(property)s and r.property = %(property)s", " and r.property = %(property)s"),
        params,
        as_dict=True,
    )
    for row in reservations:
        rows.append({
            "type": _("Arrival"), "title": row.guest_name or row.customer,
            "meta": f"{row.property} · {row.space}", "date": row.arrival_date,
            "doctype": "Property Reservation", "name": row.name,
        })
    return sorted(rows, key=lambda item: item["date"])[:8]
