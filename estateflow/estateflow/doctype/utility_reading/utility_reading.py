import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate


class UtilityReading(Document):
    def validate(self):
        meter = frappe.get_doc("Utility Meter", self.meter)
        previous = frappe.db.get_value(
            "Utility Reading",
            {
                "meter": self.meter,
                "docstatus": 1,
                "reading_date": ["<=", self.reading_date],
                "name": ["!=", self.name or ""],
            },
            ["reading", "reading_date"],
            order_by="reading_date desc, creation desc",
            as_dict=True,
        )
        self.previous_reading = flt(previous.reading if previous else meter.last_reading)
        if self.reading_type != "Opening" and flt(self.reading) < self.previous_reading:
            frappe.throw(_("Current reading cannot be lower than the previous reading."))
        self.consumption = 0 if self.reading_type == "Opening" else flt(self.reading) - self.previous_reading
        self.currency = self.currency or meter.currency
        self.amount = self.consumption * flt(meter.rate_per_unit)
        if not self.customer and meter.space:
            self.customer = frappe.db.get_value("Property Space", meter.space, "current_customer")

    def on_submit(self):
        meter = frappe.get_doc("Utility Meter", self.meter)
        if not meter.last_reading_date or getdate(self.reading_date) >= getdate(meter.last_reading_date):
            frappe.db.set_value(
                "Utility Meter",
                self.meter,
                {"last_reading": self.reading, "last_reading_date": self.reading_date},
            )

    def on_cancel(self):
        previous = frappe.db.get_value(
            "Utility Reading",
            {"meter": self.meter, "docstatus": 1, "name": ["!=", self.name]},
            ["reading", "reading_date"],
            order_by="reading_date desc, creation desc",
            as_dict=True,
        )
        frappe.db.set_value(
            "Utility Meter",
            self.meter,
            {
                "last_reading": previous.reading if previous else 0,
                "last_reading_date": previous.reading_date if previous else None,
            },
        )

    @frappe.whitelist()
    def create_sales_invoice(self, submit=None):
        self.check_permission("read")
        from estateflow.api.billing import create_utility_invoice

        return create_utility_invoice(self.name, submit=submit).name
