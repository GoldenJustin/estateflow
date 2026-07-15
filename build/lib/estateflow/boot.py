import frappe


MODE_FIELDS = {
    "landlord": "enable_landlord",
    "property_management": "enable_property_management",
    "housing_authority": "enable_housing_authority",
    "developer_sales": "enable_developer_sales",
    "brokerage": "enable_brokerage",
    "hospitality": "enable_hospitality",
    "community": "enable_community",
    "investment": "enable_investment",
}


def boot_session(bootinfo):
    """Expose only non-sensitive UI switches to Desk."""
    if not frappe.db.table_exists("EstateFlow Settings"):
        return
    settings = frappe.get_cached_doc("EstateFlow Settings")
    bootinfo.estateflow = {
        "company": settings.company,
        "property_label": settings.property_label or "Property",
        "modes": [key for key, fieldname in MODE_FIELDS.items() if settings.get(fieldname)],
    }
