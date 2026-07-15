import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate

from estateflow.api.availability import assert_space_available
from estateflow.utils import get_property_defaults, release_space_if_unused, set_space_state


class PropertyAllocation(Document):
    def validate(self):
        if self.allocation_end and self.allocation_start and getdate(self.allocation_end) <= getdate(self.allocation_start):
            frappe.throw(_("Allocation end must be after its start."))
        space = frappe.db.get_value(
            "Property Space",
            self.space,
            ["property", "allocatable", "rentable", "sellable", "currency", "base_rent", "sale_price"],
            as_dict=True,
        )
        if space:
            self.property = space.property
            self.currency = self.currency or space.currency
            if not self.amount:
                self.amount = space.sale_price if self.allocation_type == "Purchase" else space.base_rent
            if self.allocation_type == "Purchase" and not space.sellable:
                frappe.throw(_("This space is not marked as available for sale."))
            if self.allocation_type != "Purchase" and not (space.allocatable or space.rentable):
                frappe.throw(_("This space is not marked as available for housing allocation or rent."))
        if self.status in ("Approved", "Accepted") or self.docstatus == 1:
            assert_space_available(
                self.space, self.allocation_start, self.allocation_end,
                "Property Reservation", self.reservation
            )

    def before_submit(self):
        self.status = "Approved"

    def on_submit(self):
        set_space_state(self.space, "Reserved", "", "")
        if self.housing_application:
            frappe.db.set_value("Housing Application", self.housing_application, "status", "Allocated")

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        release_space_if_unused(self.space)

    @frappe.whitelist()
    def create_occupancy_agreement(self):
        self.check_permission("read")
        if self.docstatus != 1 or self.allocation_type == "Purchase":
            frappe.throw(_("Submit a rental or housing allocation first."))
        if self.occupancy_agreement:
            return self.occupancy_agreement
        item = "ESTATEFLOW-RENT"
        if not frappe.db.exists("Item", item):
            frappe.throw(_("Run EstateFlow Setup to create the standard rent Item."))
        defaults = get_property_defaults(self.property)
        agreement_type = {
            "Staff Housing": "Staff Housing",
            "Student Housing": "Student Housing",
        }.get(self.allocation_type, "Social Housing Tenancy")
        agreement = frappe.get_doc(
            {
                "doctype": "Occupancy Agreement",
                "agreement_type": agreement_type,
                "company": defaults.company,
                "customer": self.customer,
                "property": self.property,
                "space": self.space,
                "start_date": self.allocation_start,
                "end_date": self.allocation_end,
                "billing_frequency": "Monthly",
                "currency": self.currency,
                "charges": [{
                    "charge_type": "Base Rent", "item_code": item,
                    "description": _("Housing rent"), "qty": 1, "rate": self.amount,
                    "income_account": defaults.income_account, "cost_center": defaults.cost_center,
                }],
            }
        ).insert()
        self.db_set({"occupancy_agreement": agreement.name, "status": "Converted"})
        return agreement.name

    @frappe.whitelist()
    def create_sale_contract(self):
        self.check_permission("read")
        if self.docstatus != 1 or self.allocation_type != "Purchase":
            frappe.throw(_("Submit a purchase allocation first."))
        if self.sale_contract:
            return self.sale_contract
        defaults = get_property_defaults(self.property)
        contract = frappe.get_doc(
            {
                "doctype": "Property Sale Contract",
                "contract_date": self.allocation_start,
                "company": defaults.company,
                "customer": self.customer,
                "property": self.property,
                "space": self.space,
                "currency": self.currency,
                "sale_price": self.amount,
                "installments": [{
                    "milestone": _("Full purchase price"),
                    "due_date": self.allocation_end,
                    "percentage": 100,
                    "amount": self.amount,
                    "item_code": "ESTATEFLOW-PROPERTY-SALE",
                }],
            }
        ).insert()
        self.db_set({"sale_contract": contract.name, "status": "Converted"})
        return contract.name
