import frappe
from frappe import _
from frappe.model.document import Document

from estateflow.utils import refresh_property_counts


class RealEstateProperty(Document):
    def validate(self):
        if self.portfolio:
            portfolio_company = frappe.db.get_value("Property Portfolio", self.portfolio, "company")
            if portfolio_company and portfolio_company != self.company:
                frappe.throw(_("The portfolio and property must belong to the same company."))

        if self.map_location and isinstance(self.map_location, str):
            # Frappe's Geolocation field is authoritative. Latitude/longitude
            # remain optional for integrations that do not parse GeoJSON.
            pass

        if not self.currency and self.company:
            self.currency = frappe.db.get_value("Company", self.company, "default_currency")

    def on_update(self):
        refresh_property_counts(self.name)
