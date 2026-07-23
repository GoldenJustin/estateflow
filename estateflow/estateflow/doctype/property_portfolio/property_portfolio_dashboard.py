from frappe import _


def get_data():
    return {
        "fieldname": "portfolio",
        "transactions": [
            {"label": _("Assets"), "items": ["Real Estate Property"]},
        ],
    }
