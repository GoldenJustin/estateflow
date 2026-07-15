"""Live setup state for the in-app EstateFlow Guide."""

import frappe
from frappe import _

from estateflow.api.setup import DEFAULT_ITEMS, MODE_FIELDS


MODE_LABELS = {
    "landlord": "Individual / Institutional Landlord",
    "property_management": "Property Management",
    "housing_authority": "National / Social Housing",
    "developer_sales": "Developer and Unit Sales",
    "brokerage": "Agency and Brokerage",
    "hospitality": "Hotel, Lodge and Short Stay",
    "community": "HOA / Strata / Community",
    "investment": "Investment / REIT",
}


def _count(doctype, filters=None):
    return frappe.db.count(doctype, filters or {})


@frappe.whitelist()
def get_guide_context():
    if not frappe.has_permission("EstateFlow Settings", "read"):
        frappe.throw(_("You do not have permission to view the EstateFlow guide."), frappe.PermissionError)

    settings = frappe.get_single("EstateFlow Settings")
    enabled_modes = [key for key, fieldname in MODE_FIELDS.items() if settings.get(fieldname)]
    company = settings.company
    property_filters = {"company": company} if company else {}

    standard_items = [item[0] for item in DEFAULT_ITEMS]
    existing_items = set(
        frappe.get_all("Item", filters={"name": ["in", standard_items]}, pluck="name")
    ) if standard_items else set()

    counts = {
        "portfolios": _count("Property Portfolio", property_filters),
        "properties": _count("Real Estate Property", property_filters),
        "spaces": _space_count(company),
        "customers": _count("Customer"),
        "reservations": _transaction_count("Property Reservation", company),
        "agreements": _transaction_count("Occupancy Agreement", company),
        "sales": _transaction_count("Property Sale Contract", company),
        "maintenance": _transaction_count("Maintenance Request", company),
        "housing_applications": _count("Housing Application"),
    }

    checklist = [
        {
            "key": "company",
            "label": _("Choose company and business modes"),
            "description": _("Defines the organization, currency and workflows shown by EstateFlow."),
            "complete": bool(company and enabled_modes),
            "route": "Form/EstateFlow Settings/EstateFlow Settings",
            "action": _("Open settings"),
        },
        {
            "key": "items",
            "label": _("Create standard billing services"),
            "description": _("Creates non-stock Items for rent, accommodation, utilities, commissions and property sales."),
            "complete": len(existing_items) == len(standard_items),
            "detail": _("{0} of {1} services exist").format(len(existing_items), len(standard_items)),
            "route": "List/Item",
            "action": _("Review Items"),
        },
        {
            "key": "portfolio",
            "label": _("Create a portfolio"),
            "description": _("A portfolio groups one or many houses, hotels, schemes or developments."),
            "complete": counts["portfolios"] > 0,
            "detail": _("{0} portfolios").format(counts["portfolios"]),
            "route": "List/Property Portfolio",
            "action": _("Add portfolio"),
        },
        {
            "key": "property",
            "label": _("Add the first property"),
            "description": _("A property can be one house, apartment block, hotel, lodge, housing scheme or development."),
            "complete": counts["properties"] > 0,
            "detail": _("{0} properties").format(counts["properties"]),
            "route": "List/Real Estate Property",
            "action": _("Add property"),
        },
        {
            "key": "space",
            "label": _("Add units, rooms, plots or spaces"),
            "description": _("These are the actual inventory records that can be rented, booked, sold or allocated."),
            "complete": counts["spaces"] > 0,
            "detail": _("{0} spaces").format(counts["spaces"]),
            "route": "List/Property Space",
            "action": _("Add inventory"),
        },
        {
            "key": "accounting",
            "label": _("Review accounting mappings"),
            "description": _("Confirm income, maintenance, commission and security-deposit accounts before live billing."),
            "complete": bool(settings.default_income_account and settings.default_cost_center),
            "route": "Form/EstateFlow Settings/EstateFlow Settings",
            "action": _("Map accounts"),
        },
        _first_operation_check(enabled_modes, counts),
    ]

    completed = sum(1 for item in checklist if item["complete"])
    return {
        "configured": bool(company),
        "company": company,
        "currency": settings.default_currency,
        "property_label": settings.property_label or "Property",
        "enabled_modes": [{"key": key, "label": _(MODE_LABELS[key])} for key in enabled_modes],
        "counts": counts,
        "standard_items": {
            "expected": len(standard_items),
            "existing": len(existing_items),
            "missing": [item for item in standard_items if item not in existing_items],
        },
        "checklist": checklist,
        "progress": round(completed / len(checklist) * 100) if checklist else 0,
        "completed_steps": completed,
        "total_steps": len(checklist),
    }


def _space_count(company):
    if not company:
        return 0
    return frappe.db.sql(
        """
        select count(*)
        from `tabProperty Space` s
        inner join `tabReal Estate Property` p on p.name = s.property
        where p.company = %s
        """,
        company,
    )[0][0]


def _transaction_count(doctype, company):
    if not company:
        return 0
    meta = frappe.get_meta(doctype)
    if meta.has_field("company"):
        return _count(doctype, {"company": company})
    if meta.has_field("property"):
        return frappe.db.sql(
            f"""
            select count(*)
            from `tab{doctype}` d
            inner join `tabReal Estate Property` p on p.name = d.property
            where p.company = %s
            """,
            company,
        )[0][0]
    return _count(doctype)


def _first_operation_check(enabled_modes, counts):
    if "hospitality" in enabled_modes:
        complete = counts["reservations"] > 0
        label = _("Create the first booking")
        description = _("Reserve a room, confirm the guest, check in, invoice and check out.")
        route = "List/Property Reservation"
    elif "housing_authority" in enabled_modes:
        complete = counts["housing_applications"] > 0
        label = _("Capture the first housing application")
        description = _("Record an applicant, review eligibility and allocate an available unit or plot.")
        route = "List/Housing Application"
    elif "developer_sales" in enabled_modes:
        complete = counts["sales"] > 0
        label = _("Create the first property sale")
        description = _("Reserve a sellable unit and create its contract and installment schedule.")
        route = "List/Property Sale Contract"
    elif "brokerage" in enabled_modes:
        complete = _count("Property Enquiry") > 0
        label = _("Capture the first enquiry")
        description = _("Move a buyer or tenant from enquiry through viewing, offer and closing.")
        route = "List/Property Enquiry"
    else:
        complete = counts["agreements"] > 0
        label = _("Create the first occupancy agreement")
        description = _("Select a tenant and unit, then define the term and recurring rent charges.")
        route = "List/Occupancy Agreement"
    return {
        "key": "first_operation",
        "label": label,
        "description": description,
        "complete": complete,
        "route": route,
        "action": _("Start transaction"),
    }
