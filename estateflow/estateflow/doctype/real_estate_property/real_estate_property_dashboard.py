from frappe import _


def get_data():
    return {
        "fieldname": "property",
        "non_standard_fieldnames": {
            "Sales Invoice": "estateflow_property",
            "Purchase Invoice": "estateflow_property",
            "Payment Entry": "estateflow_property",
            "Material Request": "estateflow_property",
            "Purchase Order": "estateflow_property",
        },
        "transactions": [
            {"label": _("Inventory"), "items": ["Property Space", "Property Listing", "Utility Meter"]},
            {"label": _("Customers"), "items": ["Property Enquiry", "Viewing Appointment", "Property Offer", "Property Reservation"]},
            {"label": _("Contracts"), "items": ["Occupancy Agreement", "Property Sale Contract", "Property Allocation"]},
            {"label": _("Facilities"), "items": ["Maintenance Request", "Property Work Order", "Property Inspection"]},
            {"label": _("Accounting"), "items": ["Sales Invoice", "Purchase Invoice", "Payment Entry"]},
            {"label": _("Supply Chain"), "items": ["Material Request", "Purchase Order"]},
        ],
    }
