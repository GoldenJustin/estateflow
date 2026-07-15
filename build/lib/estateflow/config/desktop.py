from frappe import _


def get_data():
    return [
        {
            "module_name": "EstateFlow",
            "type": "module",
            "label": _("EstateFlow"),
            "icon": "octicon octicon-home",
            "color": "#4f46e5",
            "description": _("Properties, housing, hospitality, leasing, sales and facilities"),
        }
    ]
