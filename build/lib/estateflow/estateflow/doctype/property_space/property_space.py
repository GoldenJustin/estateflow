import frappe
from frappe import _
from frappe.model.document import Document

from estateflow.utils import get_property_defaults, refresh_property_counts


class PropertySpace(Document):
    def validate(self):
        defaults = get_property_defaults(self.property)
        if not defaults:
            return
        if self.parent_space:
            parent_property = frappe.db.get_value("Property Space", self.parent_space, "property")
            if parent_property != self.property:
                frappe.throw(_("A parent space must belong to the same property."))
            if self.parent_space == self.name:
                frappe.throw(_("A space cannot be its own parent."))

        self.currency = self.currency or defaults.currency
        self.cost_center = self.cost_center or defaults.cost_center
        self.project = self.project or defaults.project
        self.income_account = self.income_account or defaults.income_account

        if self.bookable and self.housekeeping_status == "Not Applicable":
            self.housekeeping_status = "Clean"

    def after_insert(self):
        refresh_property_counts(self.property)

    def on_update(self):
        refresh_property_counts(self.property)

    def on_trash(self):
        property_name = self.property
        frappe.flags.estateflow_refresh_property = property_name

    def after_delete(self):
        property_name = getattr(frappe.flags, "estateflow_refresh_property", None)
        if property_name:
            refresh_property_counts(property_name)
