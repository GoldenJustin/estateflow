import frappe
from frappe import _
from frappe.utils import getdate, nowdate


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not frappe.has_permission("Occupancy Agreement", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    columns = [
        {"label": _("Agreement"), "fieldname": "agreement", "fieldtype": "Link", "options": "Occupancy Agreement", "width": 140},
        {"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Real Estate Property", "width": 170},
        {"label": _("Unit / Space"), "fieldname": "space", "fieldtype": "Link", "options": "Property Space", "width": 145},
        {"label": _("Tenant / Occupant"), "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
        {"label": _("Type"), "fieldname": "agreement_type", "fieldtype": "Data", "width": 130},
        {"label": _("Start"), "fieldname": "start_date", "fieldtype": "Date", "width": 95},
        {"label": _("End"), "fieldname": "end_date", "fieldtype": "Date", "width": 95},
        {"label": _("Frequency"), "fieldname": "billing_frequency", "fieldtype": "Data", "width": 95},
        {"label": _("Currency"), "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
        {"label": _("Recurring Amount"), "fieldname": "recurring_amount", "fieldtype": "Currency", "options": "currency", "width": 135},
        {"label": _("Deposit"), "fieldname": "security_deposit_amount", "fieldtype": "Currency", "options": "currency", "width": 115},
        {"label": _("Next Invoice"), "fieldname": "next_invoice_date", "fieldtype": "Date", "width": 105},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 95},
    ]
    values = {"as_on": getdate(filters.as_on_date or nowdate())}
    conditions = ["a.docstatus = 1", "a.start_date <= %(as_on)s", "a.end_date >= %(as_on)s"]
    if filters.company:
        conditions.append("a.company = %(company)s"); values["company"] = filters.company
    if filters.property:
        conditions.append("a.property = %(property)s"); values["property"] = filters.property
    if filters.status:
        conditions.append("a.status = %(status)s"); values["status"] = filters.status
    data = frappe.db.sql(
        f"""select a.name as agreement, a.property, a.space, a.customer, a.agreement_type,
                   a.start_date, a.end_date, a.billing_frequency, a.currency,
                   coalesce(sum(c.qty * c.rate), 0) as recurring_amount,
                   a.security_deposit_amount, a.next_invoice_date, a.status
            from `tabOccupancy Agreement` a
            left join `tabAgreement Charge` c on c.parent = a.name and c.parenttype = 'Occupancy Agreement'
            where {' and '.join(conditions)}
            group by a.name order by a.property, a.space""",
        values, as_dict=True,
    )
    return columns, data
