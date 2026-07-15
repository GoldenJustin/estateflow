from frappe import _


def get_data():
    return {
        "fieldname": "reservation",
        "non_standard_fieldnames": {"Sales Invoice": "estateflow_reservation", "Payment Entry": "estateflow_reservation"},
        "transactions": [{"label": _("Billing"), "items": ["Sales Invoice", "Payment Entry"]}],
    }
