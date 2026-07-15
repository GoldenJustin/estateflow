import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from estateflow.utils import calculate_sla_due, get_property_defaults


class MaintenanceRequest(Document):
    def validate(self):
        self.reported_on = self.reported_on or now_datetime()
        self.sla_due_on = self.sla_due_on or calculate_sla_due(self.priority, self.reported_on)
        if self.space:
            space_property = frappe.db.get_value("Property Space", self.space, "property")
            if space_property and space_property != self.property:
                frappe.throw(_("The selected space does not belong to this property."))
        if self.status in ("Resolved", "Closed") and not self.resolution:
            frappe.throw(_("Enter the resolution before resolving this request."))
        if self.status == "Resolved" and not self.resolution_date:
            self.resolution_date = now_datetime()

    @frappe.whitelist()
    def create_work_order(self):
        self.check_permission("write")
        if self.work_order and frappe.db.exists("Property Work Order", self.work_order):
            return self.work_order
        defaults = get_property_defaults(self.property)
        work_order = frappe.get_doc(
            {
                "doctype": "Property Work Order",
                "subject": self.subject,
                "work_order_type": "Corrective Maintenance" if self.request_type != "Turnover" else "Unit Turnover",
                "status": "Draft",
                "maintenance_request": self.name,
                "property": self.property,
                "space": self.space,
                "priority": self.priority,
                "assigned_to": self.assigned_to,
                "currency": defaults.currency,
                "instructions": self.description,
            }
        ).insert()
        self.db_set({"work_order": work_order.name, "status": "Assigned"})
        return work_order.name
