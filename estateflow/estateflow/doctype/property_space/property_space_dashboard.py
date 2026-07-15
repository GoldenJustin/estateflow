from frappe import _


def get_data():
    return {
        "fieldname": "space",
        "non_standard_fieldnames": {
            "Sales Invoice": "estateflow_space",
            "Purchase Invoice": "estateflow_space",
            "Payment Entry": "estateflow_space",
        },
        "transactions": [
            {"label": _("Occupancy"), "items": ["Property Reservation", "Occupancy Agreement", "Property Allocation"]},
            {"label": _("Sales"), "items": ["Property Listing", "Property Offer", "Property Sale Contract"]},
            {"label": _("Facilities"), "items": ["Maintenance Request", "Property Work Order", "Property Inspection", "Utility Meter"]},
            {"label": _("Accounting"), "items": ["Sales Invoice", "Purchase Invoice", "Payment Entry"]},
        ],
    }
