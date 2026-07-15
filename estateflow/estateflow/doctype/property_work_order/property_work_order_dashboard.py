from frappe import _


def get_data():
    return {
        "fieldname": "estateflow_work_order",
        "non_standard_fieldnames": {
            "Material Request": "estateflow_work_order",
            "Purchase Order": "estateflow_work_order",
            "Purchase Receipt": "estateflow_work_order",
            "Purchase Invoice": "estateflow_work_order",
            "Stock Entry": "estateflow_work_order",
        },
        "transactions": [
            {"label": _("Procurement"), "items": ["Material Request", "Purchase Order", "Purchase Receipt", "Purchase Invoice"]},
            {"label": _("Stock"), "items": ["Stock Entry"]},
        ],
    }
