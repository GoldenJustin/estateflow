import frappe
from frappe import _
from frappe.model.document import Document


class PropertyInspection(Document):
    def validate(self):
        if self.space:
            property_name = frappe.db.get_value("Property Space", self.space, "property")
            if property_name != self.property:
                frappe.throw(_("The selected space does not belong to this property."))
        applicable = [row for row in self.items if row.condition != "Not Applicable"]
        self.score = (sum(1 for row in applicable if row.passed) / len(applicable) * 100) if applicable else 0

    def before_submit(self):
        self.status = "Completed"

    @frappe.whitelist()
    def create_maintenance_requests(self):
        self.check_permission("read")
        created = []
        for row in self.items:
            if not row.maintenance_required:
                continue
            subject = _("Inspection finding: {0}").format(row.area_or_item)
            existing = frappe.db.exists(
                "Maintenance Request",
                {"property": self.property, "space": self.space, "subject": subject, "status": ["not in", ["Closed", "Cancelled"]]},
            )
            if existing:
                created.append(existing)
                continue
            request = frappe.get_doc(
                {
                    "doctype": "Maintenance Request",
                    "subject": subject,
                    "property": self.property,
                    "space": self.space,
                    "category": "Defect",
                    "request_type": "Inspection Finding",
                    "priority": "Medium" if row.condition in ("Fair", "Poor") else "High",
                    "reported_by_type": "Inspection",
                    "reported_by_name": self.inspector,
                    "description": row.notes or _("Condition recorded as {0}").format(row.condition),
                }
            ).insert()
            created.append(request.name)
        return created
