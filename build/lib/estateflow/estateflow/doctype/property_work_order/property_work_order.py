import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, now_datetime, nowdate

from estateflow.utils import get_estateflow_settings, get_property_defaults


class PropertyWorkOrder(Document):
    def validate(self):
        defaults = get_property_defaults(self.property)
        self.currency = self.currency or defaults.currency or get_estateflow_settings().default_currency
        if self.space:
            space_property = frappe.db.get_value("Property Space", self.space, "property")
            if space_property != self.property:
                frappe.throw(_("The selected space does not belong to this property."))
        if self.planned_start and self.planned_end and self.planned_end < self.planned_start:
            frappe.throw(_("Planned end cannot be before planned start."))
        if not self.assigned_to and not self.supplier:
            frappe.throw(_("Assign an internal technician or a contractor."))

    def before_submit(self):
        if self.status == "Draft":
            self.status = "Approved"

    def on_submit(self):
        if self.maintenance_request:
            frappe.db.set_value(
                "Maintenance Request",
                self.maintenance_request,
                {"status": "Assigned", "work_order": self.name},
            )

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        if self.maintenance_request:
            frappe.db.set_value("Maintenance Request", self.maintenance_request, "status", "Open")

    @frappe.whitelist()
    def start_work(self):
        self.check_permission("write")
        if self.docstatus != 1:
            frappe.throw(_("Submit the work order before starting work."))
        self.db_set({"status": "In Progress", "actual_start": now_datetime()})
        if self.maintenance_request:
            frappe.db.set_value("Maintenance Request", self.maintenance_request, "status", "In Progress")
        return self.name

    @frappe.whitelist()
    def complete_work(self, completion_notes=None):
        self.check_permission("write")
        if self.docstatus != 1:
            frappe.throw(_("Submit the work order before completing it."))
        if not completion_notes and not self.completion_notes:
            frappe.throw(_("Enter completion notes."))
        self.db_set(
            {
                "status": "Completed",
                "actual_end": now_datetime(),
                "completion_notes": completion_notes or self.completion_notes,
            }
        )
        if self.maintenance_request:
            frappe.db.set_value(
                "Maintenance Request",
                self.maintenance_request,
                {"status": "Resolved", "resolution": completion_notes or self.completion_notes, "resolution_date": now_datetime()},
            )
        if self.work_order_type in ("Housekeeping", "Unit Turnover", "Cleaning") and self.space:
            frappe.db.set_value("Property Space", self.space, "housekeeping_status", "Clean")
        return self.name

    @frappe.whitelist()
    def create_material_request(self):
        self.check_permission("read")
        if not self.materials:
            frappe.throw(_("Add required materials first."))

        defaults = get_property_defaults(self.property)
        request = frappe.new_doc("Material Request")
        request.material_request_type = "Purchase"
        request.company = defaults.company or get_estateflow_settings().company
        request.schedule_date = add_days(nowdate(), 1)
        if request.meta.has_field("estateflow_property"):
            request.estateflow_property = self.property
            request.estateflow_space = self.space
            request.estateflow_work_order = self.name
        for row in self.materials:
            if row.material_request:
                continue
            request.append(
                "items",
                {
                    "item_code": row.item_code,
                    "qty": row.required_qty,
                    "schedule_date": request.schedule_date,
                    "warehouse": row.source_warehouse or defaults.warehouse,
                },
            )
        if not request.items:
            frappe.throw(_("All material rows already have a Material Request."))
        request.set_missing_values()
        request.insert()
        for row in self.materials:
            if not row.material_request:
                frappe.db.set_value("Work Order Material", row.name, "material_request", request.name)
        return request.name
