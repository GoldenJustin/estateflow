app_name = "estateflow"
app_title = "EstateFlow"
app_publisher = "EstateFlow contributors"
app_description = "Universal real estate, housing, hospitality and property operations for ERPNext"
app_email = "hello@example.com"
app_license = "MIT"

required_apps = ["erpnext"]

app_include_css = [
    "/assets/estateflow/css/estateflow.css",
    "/assets/estateflow/css/estateflow-guide.css",
]
app_include_js = ["/assets/estateflow/js/estateflow.js"]
extend_bootinfo = "estateflow.boot.boot_session"

before_install = "estateflow.install.before_install"
after_install = "estateflow.install.after_install"
after_migrate = "estateflow.install.after_migrate"

scheduler_events = {
    "daily": [
        "estateflow.api.billing.run_daily_billing",
        "estateflow.api.operations.run_daily_operations",
        "estateflow.api.notifications.run_daily_notifications",
    ]
}

doc_events = {
    "Sales Invoice": {
        "on_submit": "estateflow.api.billing_tracking.on_sales_invoice_submit",
        "on_update_after_submit": "estateflow.api.billing_tracking.on_sales_invoice_update",
        "on_cancel": "estateflow.api.billing_tracking.on_sales_invoice_cancel",
    },
    "Payment Entry": {
        "on_submit": "estateflow.api.billing_tracking.on_payment_entry_submit",
        "on_cancel": "estateflow.api.billing_tracking.on_payment_entry_cancel",
    },
}

website_route_rules = [
    {"from_route": "/properties/<name>", "to_route": "property-listing"}
]

standard_portal_menu_items = [
    {"title": "My Estate", "route": "/my-estate", "role": "EstateFlow Portal User"}
]
# Kept for compatibility with Frappe releases that read the older hook name.
portal_menu_items = standard_portal_menu_items

fixtures = [
    {
        "dt": "Role",
        "filters": [["name", "in", [
            "EstateFlow Administrator",
            "Portfolio Manager",
            "Property Manager",
            "Leasing Officer",
            "Estate Agent",
            "Front Desk Officer",
            "Housing Officer",
            "Facilities Officer",
            "EstateFlow Portal User",
        ]]],
    }
]
