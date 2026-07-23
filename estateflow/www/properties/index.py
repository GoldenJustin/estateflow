import frappe
from frappe import _

no_cache = 1


def get_context(context):
    context.title = _("Available Properties")
    filters = {"status": "Active", "publish_on_website": 1}
    listing_type = frappe.form_dict.get("type")
    if listing_type:
        filters["listing_type"] = listing_type
    rows = frappe.get_all(
        "Property Listing",
        filters=filters,
        fields=[
            "name", "listing_title", "listing_type", "property", "space", "currency",
            "asking_price", "available_from", "public_description", "featured_image",
            "website_route", "channel",
        ],
        order_by="modified desc",
        limit_page_length=200,
    )
    search = (frappe.form_dict.get("q") or "").strip().lower()
    if search:
        rows = [row for row in rows if search in " ".join([
            row.listing_title or "", row.property or "", row.space or "", row.public_description or ""
        ]).lower()]
    context.listings = rows
    context.listing_type = listing_type
    context.search = search
    return context
