from frappe import _


def get_data():
    return {
        "fieldname": "agreement",
        "non_standard_fieldnames": {
            "Sales Invoice": "estateflow_agreement",
            "Payment Entry": "estateflow_agreement",
            "Journal Entry": "estateflow_agreement",
        },
        "transactions": [
            {"label": _("Billing"), "items": ["Sales Invoice", "Payment Entry"]},
            {"label": _("Deposit"), "items": ["Security Deposit Transaction", "Journal Entry"]},
        ],
    }
