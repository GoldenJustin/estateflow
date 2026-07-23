import frappe
from frappe import _

no_cache = 1


def get_context(context):
    route_name = frappe.form_dict.get("name")
    full_route = f"properties/{route_name}" if route_name else None
    listing_name = frappe.form_dict.get("listing")
    filters = {"status": "Active", "publish_on_website": 1}
    if listing_name:
        filters["name"] = listing_name
    elif full_route:
        filters["website_route"] = full_route
    else:
        raise frappe.DoesNotExistError
    name = frappe.db.get_value("Property Listing", filters, "name")
    if not name:
        raise frappe.DoesNotExistError
    context.doc = frappe.get_doc("Property Listing", name)
    context.property_doc = frappe.get_doc("Real Estate Property", context.doc.property)
    context.space_doc = frappe.get_doc("Property Space", context.doc.space) if context.doc.space else None
    context.title = context.doc.listing_title
    return context
