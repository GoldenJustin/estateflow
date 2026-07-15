import frappe
from frappe import _


def execute(filters=None):
    filters = frappe._dict(filters or {})
    if not frappe.has_permission("Property Space", "read"):
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    columns = [
        {"label": _("Property"), "fieldname": "property", "fieldtype": "Link", "options": "Real Estate Property", "width": 180},
        {"label": _("Unit / Room / Space"), "fieldname": "name", "fieldtype": "Link", "options": "Property Space", "width": 170},
        {"label": _("Name"), "fieldname": "space_name", "fieldtype": "Data", "width": 150},
        {"label": _("Type"), "fieldname": "space_type", "fieldtype": "Data", "width": 120},
        {"label": _("Floor / Zone"), "fieldname": "floor_or_zone", "fieldtype": "Data", "width": 100},
        {"label": _("Occupancy"), "fieldname": "occupancy_status", "fieldtype": "Data", "width": 125},
        {"label": _("Housekeeping"), "fieldname": "housekeeping_status", "fieldtype": "Data", "width": 110},
        {"label": _("Currency"), "fieldname": "currency", "fieldtype": "Link", "options": "Currency", "width": 80},
        {"label": _("Rent"), "fieldname": "base_rent", "fieldtype": "Currency", "options": "currency", "width": 110},
        {"label": _("Nightly"), "fieldname": "nightly_rate", "fieldtype": "Currency", "options": "currency", "width": 110},
        {"label": _("Sale Price"), "fieldname": "sale_price", "fieldtype": "Currency", "options": "currency", "width": 125},
        {"label": _("Current Occupant"), "fieldname": "current_customer", "fieldtype": "Link", "options": "Customer", "width": 160},
    ]
    conditions, values = ["1=1"], {}
    if filters.company:
        conditions.append("p.company = %(company)s"); values["company"] = filters.company
    if filters.property:
        conditions.append("s.property = %(property)s"); values["property"] = filters.property
    if filters.space_type:
        conditions.append("s.space_type = %(space_type)s"); values["space_type"] = filters.space_type
    if filters.occupancy_status:
        conditions.append("s.occupancy_status = %(occupancy_status)s"); values["occupancy_status"] = filters.occupancy_status
    use_field = {"Long-term Rent": "rentable", "Sale": "sellable", "Short Stay": "bookable", "Housing Allocation": "allocatable"}.get(filters.use)
    if use_field:
        conditions.append(f"s.{use_field} = 1")
    data = frappe.db.sql(
        f"""select s.name, s.space_name, s.property, s.space_type, s.floor_or_zone,
                   s.occupancy_status, s.housekeeping_status, s.currency, s.base_rent,
                   s.nightly_rate, s.sale_price, s.current_customer
            from `tabProperty Space` s
            inner join `tabReal Estate Property` p on p.name = s.property
            where {' and '.join(conditions)} order by s.property, s.space_name""",
        values, as_dict=True,
    )
    return columns, data
