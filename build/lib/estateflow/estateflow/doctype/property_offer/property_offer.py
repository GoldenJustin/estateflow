import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate


class PropertyOffer(Document):
    def validate(self):
        if self.space:
            property_name = frappe.db.get_value("Property Space", self.space, "property")
            if property_name != self.property:
                frappe.throw(_("The selected space does not belong to this property."))
        if self.start_date and self.end_date and getdate(self.end_date) <= getdate(self.start_date):
            frappe.throw(_("Offer end date must be after its start date."))
        if self.valid_until and getdate(self.valid_until) < getdate(nowdate()) and self.status not in ("Accepted", "Rejected", "Withdrawn", "Expired"):
            self.status = "Expired"

    def before_submit(self):
        if self.status == "Draft":
            self.status = "Submitted"

    def on_cancel(self):
        self.db_set("status", "Withdrawn")

    @frappe.whitelist()
    def accept_offer(self):
        self.check_permission("write")
        if self.docstatus != 1:
            frappe.throw(_("Submit the offer before accepting it."))
        if self.status in ("Rejected", "Withdrawn", "Expired"):
            frappe.throw(_("This offer can no longer be accepted."))
        self.db_set("status", "Accepted")
        return self.name

    @frappe.whitelist()
    def create_reservation(self):
        self.check_permission("read")
        if self.docstatus != 1 or self.status != "Accepted":
            frappe.throw(_("Accept the submitted offer first."))
        existing = frappe.db.get_value(
            "Property Reservation", {"offer": self.name, "docstatus": ["<", 2]}, "name"
        )
        if existing:
            return existing
        start = self.start_date or nowdate()
        end = self.end_date or self.valid_until
        if not end or getdate(end) <= getdate(start):
            end = add_days(start, 1)
        reservation_type = {
            "Long-term Rent": "Long-term Lease Hold",
            "Purchase": "Property Sale Hold",
            "Short Stay": "Hotel / Lodge Stay",
        }[self.offer_type]
        reservation = frappe.get_doc(
            {
                "doctype": "Property Reservation",
                "reservation_type": reservation_type,
                "status": "Tentative",
                "source": "Agent" if self.agent else "Direct",
                "property": self.property,
                "space": self.space,
                "offer": self.name,
                "agent": self.agent,
                "customer": self.customer,
                "arrival_date": start,
                "departure_date": end,
                "currency": self.currency,
                "base_rate": self.offered_amount,
            }
        ).insert()
        return reservation.name
