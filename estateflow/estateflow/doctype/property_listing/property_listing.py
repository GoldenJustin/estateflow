import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, nowdate


class PropertyListing(Document):
    def validate(self):
        if self.space:
            space_property = frappe.db.get_value("Property Space", self.space, "property")
            if space_property != self.property:
                frappe.throw(_("The selected space does not belong to this property."))
        if self.valid_until and getdate(self.valid_until) < getdate(nowdate()) and self.status == "Active":
            self.status = "Expired"
        slug = re.sub(r"[^a-z0-9]+", "-", (self.listing_title or self.name or "property").lower()).strip("-")
        suffix = (self.name or "")[-5:].lower()
        self.website_route = f"properties/{slug}-{suffix}" if suffix else f"properties/{slug}"
        if self.publish_on_website and not self.featured_image and self.space:
            self.featured_image = frappe.db.get_value("Property Space", self.space, "space_image")
        if self.publish_on_website and not self.featured_image:
            self.featured_image = frappe.db.get_value("Real Estate Property", self.property, "property_image")

    @frappe.whitelist()
    def activate_listing(self):
        self.check_permission("write")
        self.status = "Active"
        self.publish_on_website = 1
        self.save()
        return self.website_route
