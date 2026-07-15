import frappe
from frappe import _
from frappe.utils import date_diff, getdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not frappe.has_permission("Occupancy Agreement", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    columns = [
        {"label": _("Agreement"), "fieldname": "name", "fieldtype": "Link", "options": "Occupancy Agreement", "width": 145},
        {"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Real Estate Property", "width": 175},
        {"label": _("Unit / Space"), "fieldname": "space", "fieldtype": "Link", "options": "Property Space", "width": 145},
        {"label": _("Tenant"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Expiry"), "fieldname": "end_date", "fieldtype": "Date", "width": 100},
        {"label": _("Days Remaining"), "fieldname": "days_remaining", "fieldtype": "Int", "width": 110},
        {"label": _("Notice Days"), "fieldname": "notice_period_days", "fieldtype": "Int", "width": 100},
        {"label": _("Renewal"), "fieldname": "renewal_option", "fieldtype": "Check", "width": 80},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 95},
    ]
    values = {"from_date": filters.from_date, "to_date": filters.to_date}
    conditions = ["a.docstatus = 1", "a.status in ('Active', 'Notice Given')", "a.end_date between %(from_date)s and %(to_date)s"]
    if filters.company:
        conditions.append("a.company = %(company)s"); values["company"] = filters.company
    if filters.property:
        conditions.append("a.property = %(property)s"); values["property"] = filters.property
    data = frappe.db.sql(
        f"""select a.name, a.property, a.space, a.customer, a.end_date,
                   datediff(a.end_date, curdate()) as days_remaining,
                   a.notice_period_days, a.renewal_option, a.status
            from `tabOccupancy Agreement` a where {' and '.join(conditions)}
            order by a.end_date""",
        values, as_dict=True,
    )
    return columns, data
