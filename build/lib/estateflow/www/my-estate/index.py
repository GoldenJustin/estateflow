import frappe
from frappe import _
from frappe.utils import nowdate

no_cache = 1


def get_context(context):
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/my-estate"
        raise frappe.Redirect

    context.title = _("My Estate")
    context.show_sidebar = False
    context.customers = _customers_for_user(frappe.session.user)
    context.reservations = []
    context.agreements = []
    context.invoices = []
    if not context.customers:
        context.no_customer = True
        return context

    customer_filter = ["in", context.customers]
    context.reservations = frappe.get_all(
        "Property Reservation",
        filters={"customer": customer_filter, "docstatus": ["<", 2]},
        fields=["name", "reservation_type", "property", "space", "arrival_date", "departure_date", "status", "grand_total", "currency"],
        order_by="arrival_date desc",
        limit_page_length=30,
    )
    context.agreements = frappe.get_all(
        "Occupancy Agreement",
        filters={"customer": customer_filter, "docstatus": 1},
        fields=["name", "agreement_type", "property", "space", "start_date", "end_date", "status", "currency"],
        order_by="end_date desc",
        limit_page_length=30,
    )
    context.invoices = frappe.get_all(
        "Sales Invoice",
        filters={"customer": customer_filter, "docstatus": 1, "estateflow_property": ["is", "set"]},
        fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount", "currency", "status", "estateflow_property"],
        order_by="posting_date desc",
        limit_page_length=30,
    )
    context.today = nowdate()
    return context


def _customers_for_user(user):
    contacts = frappe.get_all("Contact", filters={"user": user}, pluck="name")
    if not contacts:
        return []
    return frappe.get_all(
        "Dynamic Link",
        filters={"parent": ["in", contacts], "parenttype": "Contact", "link_doctype": "Customer"},
        pluck="link_name",
    )
