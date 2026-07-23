from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import date_diff, flt, get_datetime, getdate, now_datetime

from estateflow.api.availability import assert_space_available
from estateflow.utils import (
    get_estateflow_settings,
    get_property_defaults,
    release_space_if_unused,
    set_space_state,
)


class PropertyReservation(Document):
    def validate(self):
        self._set_defaults()
        self._validate_dates_and_capacity()
        self._calculate_totals()
        if self.status in ("Tentative", "Confirmed", "Checked In"):
            settings = get_estateflow_settings()
            if settings.prevent_double_booking:
                assert_space_available(
                    self.space,
                    self.arrival_date,
                    self.departure_date,
                    "Property Reservation",
                    None if self.is_new() else self.name,
                )

    def before_submit(self):
        if self.status in ("Draft", "Tentative"):
            self.status = "Confirmed"
        assert_space_available(
            self.space,
            self.arrival_date,
            self.departure_date,
            "Property Reservation",
            self.name,
        )

    def on_submit(self):
        if self.status == "Checked In":
            set_space_state(self.space, "Occupied", self.customer, "")
        else:
            set_space_state(self.space, "Reserved", "", "")
        if self.status == "Confirmed":
            from estateflow.api.notifications import send_reservation_confirmation
            send_reservation_confirmation(self)

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        release_space_if_unused(self.space)

    def _set_defaults(self):
        space = frappe.db.get_value(
            "Property Space",
            self.space,
            ["property", "currency", "nightly_rate", "base_rent", "max_adults", "max_children"],
            as_dict=True,
        )
        if not space:
            return
        if self.property != space.property:
            self.property = space.property
        defaults = get_property_defaults(self.property)
        settings = get_estateflow_settings()
        self.currency = self.currency or space.currency or defaults.currency or settings.default_currency
        if not self.base_rate:
            self.base_rate = space.nightly_rate if self.reservation_type == "Hotel / Lodge Stay" else space.base_rent
        self.check_in_time = self.check_in_time or settings.default_check_in_time
        self.check_out_time = self.check_out_time or settings.default_check_out_time

    def _validate_dates_and_capacity(self):
        if not self.arrival_date or not self.departure_date:
            return
        if getdate(self.departure_date) <= getdate(self.arrival_date):
            frappe.throw(_("Departure / hold end must be after arrival / hold start."))

        self.number_of_nights = max(1, date_diff(self.departure_date, self.arrival_date))
        limits = frappe.db.get_value(
            "Property Space", self.space, ["max_adults", "max_children"], as_dict=True
        )
        if limits:
            if limits.max_adults and self.adults > limits.max_adults:
                frappe.throw(_("This space allows at most {0} adults.").format(limits.max_adults))
            if limits.max_children and self.children > limits.max_children:
                frappe.throw(_("This space allows at most {0} children.").format(limits.max_children))

    def _calculate_totals(self):
        periods = self.number_of_nights if self.reservation_type == "Hotel / Lodge Stay" else 1
        base_total = flt(self.base_rate) * flt(periods)
        charge_total = 0
        for row in self.charges:
            row.qty = row.qty or 1
            row.amount = flt(row.qty) * flt(row.rate)
            charge_total += row.amount
        self.subtotal = base_total + charge_total
        self.grand_total = max(0, self.subtotal - flt(self.discount_amount))

    @frappe.whitelist()
    def confirm_reservation(self):
        self.check_permission("submit" if self.docstatus == 0 else "write")
        if self.docstatus == 0:
            self.status = "Confirmed"
            self.save()
            self.submit()
        else:
            self.db_set("status", "Confirmed")
            set_space_state(self.space, "Reserved", "", "")
        return self.name

    @frappe.whitelist()
    def check_in(self):
        self.check_permission("write")
        if self.docstatus != 1:
            frappe.throw(_("Confirm and submit the reservation before check-in."))
        if self.status not in ("Confirmed", "Tentative"):
            frappe.throw(_("Only a confirmed reservation can be checked in."))
        if getdate(self.departure_date) < getdate():
            frappe.throw(_("This reservation has already passed its departure date."))

        self.status = "Checked In"
        self.actual_check_in = now_datetime()
        self.save()
        set_space_state(self.space, "Occupied", self.customer, "")
        return self.name

    @frappe.whitelist()
    def check_out(self):
        self.check_permission("write")
        if self.docstatus != 1 or self.status != "Checked In":
            frappe.throw(_("Only a checked-in reservation can be checked out."))
        self.status = "Checked Out"
        self.actual_check_out = now_datetime()
        self.save()
        settings = get_estateflow_settings()
        housekeeping = "Dirty" if settings.mark_space_dirty_on_checkout else None
        set_space_state(self.space, "Available", "", "", housekeeping)
        return self.name

    @frappe.whitelist()
    def create_sales_invoice(self, submit=None):
        self.check_permission("read")
        from estateflow.api.billing import create_reservation_invoice

        invoice = create_reservation_invoice(self.name, submit=submit)
        return invoice.name
