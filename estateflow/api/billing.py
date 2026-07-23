"""Accounting automation for rent, stays, utilities and property sales."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, add_months, cint, flt, getdate, nowdate

from estateflow.utils import get_estateflow_settings, get_property_defaults


FREQUENCY_MONTHS = {
    "Monthly": 1,
    "Quarterly": 3,
    "Half-yearly": 6,
    "Yearly": 12,
}


def _should_submit(submit=None):
    if submit is None or str(submit) == "":
        return cint(get_estateflow_settings().auto_submit_invoices)
    return cint(submit)


def _next_period(date, frequency):
    if frequency == "One Time":
        return None
    return add_months(date, FREQUENCY_MONTHS.get(frequency, 1))


def _require_item(item_code, purpose):
    if not item_code or not frappe.db.exists("Item", item_code):
        frappe.throw(
            _("An Item is required for {0}. Run EstateFlow Setup or select an Item in the document.").format(purpose)
        )
    return item_code


def _apply_estateflow_dimensions(invoice, *, property_name=None, space=None, agreement=None,
                                  reservation=None, sale_contract=None, period_start=None, period_end=None,
                                  billing_source=None, milestone_row=None):
    values = {
        "estateflow_property": property_name,
        "estateflow_space": space,
        "estateflow_agreement": agreement,
        "estateflow_reservation": reservation,
        "estateflow_sale_contract": sale_contract,
        "estateflow_billing_period_start": period_start,
        "estateflow_billing_period_end": period_end,
        "estateflow_billing_source": billing_source,
        "estateflow_milestone_row": milestone_row,
    }
    for fieldname, value in values.items():
        if value is not None and invoice.meta.has_field(fieldname):
            invoice.set(fieldname, value)


def _insert_invoice(invoice, submit=None):
    invoice.set_missing_values()
    invoice.insert()
    if _should_submit(submit):
        invoice.submit()
    from estateflow.api.billing_tracking import sync_invoice_billing_event
    sync_invoice_billing_event(invoice)
    return invoice


def generate_agreement_invoice(agreement_name, billing_date=None, submit=None):
    agreement = frappe.get_doc("Occupancy Agreement", agreement_name)
    agreement.check_permission("read")
    if agreement.docstatus != 1 or agreement.status not in ("Pending Activation", "Active", "Notice Given"):
        frappe.throw(_("Only a current submitted agreement can be billed."))
    if not agreement.charges:
        frappe.throw(_("This agreement has no recurring charges to invoice."))

    period_start = getdate(billing_date or agreement.next_invoice_date or agreement.start_date)
    if period_start > getdate(agreement.end_date):
        frappe.throw(_("The agreement has no billable period remaining."))
    next_date = _next_period(period_start, agreement.billing_frequency)
    period_end = min(getdate(agreement.end_date), add_days(next_date, -1)) if next_date else getdate(agreement.end_date)

    existing = frappe.db.get_value(
        "Sales Invoice",
        {
            "estateflow_agreement": agreement.name,
            "estateflow_billing_period_start": period_start,
            "docstatus": ["<", 2],
        },
        "name",
    )
    if existing:
        invoice = frappe.get_doc("Sales Invoice", existing)
        from estateflow.api.billing_tracking import sync_invoice_billing_event
        sync_invoice_billing_event(invoice)
        return invoice

    defaults = get_property_defaults(agreement.property)
    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = agreement.customer
    invoice.company = agreement.company
    invoice.currency = agreement.currency
    invoice.posting_date = min(getdate(nowdate()), period_start)
    invoice.due_date = add_days(invoice.posting_date, agreement.invoice_due_days or 0)
    _apply_estateflow_dimensions(
        invoice,
        property_name=agreement.property,
        space=agreement.space,
        agreement=agreement.name,
        period_start=period_start,
        period_end=period_end,
        billing_source="Recurring Charge",
    )

    for charge in agreement.charges:
        invoice.append(
            "items",
            {
                "item_code": _require_item(charge.item_code, charge.charge_type),
                "description": charge.description,
                "qty": charge.qty or 1,
                "rate": charge.rate,
                "income_account": charge.income_account or defaults.income_account,
                "cost_center": charge.cost_center or defaults.cost_center,
            },
        )
    _insert_invoice(invoice, submit)

    next_invoice_date = next_date if next_date and next_date <= getdate(agreement.end_date) else None
    agreement.db_set({"next_invoice_date": next_invoice_date, "last_invoice_date": invoice.posting_date})
    return invoice


def _agreement_trigger_date(agreement):
    if not agreement.next_invoice_date:
        return None
    if agreement.billing_start_policy == "Days Before Period Start":
        return getdate(add_days(agreement.next_invoice_date, -(agreement.invoice_lead_days or 0)))
    # On Activation affects the first invoice; later periods trigger on period start.
    if agreement.billing_start_policy == "On Activation" and not agreement.last_invoice_date:
        return getdate(agreement.start_date) if agreement.status == "Pending Activation" else getdate(nowdate())
    return getdate(agreement.next_invoice_date)


def generate_agreement_milestone_invoices(agreement_name, as_of_date=None, submit=None):
    agreement = frappe.get_doc("Occupancy Agreement", agreement_name)
    if agreement.docstatus != 1 or agreement.status not in ("Pending Activation", "Active", "Notice Given"):
        frappe.throw(_("Only a current submitted agreement can be billed."))
    cutoff = getdate(as_of_date or nowdate())
    if agreement.billing_start_policy == "Days Before Period Start":
        cutoff = add_days(cutoff, agreement.invoice_lead_days or 0)
    defaults = get_property_defaults(agreement.property)
    created = []
    for row in agreement.payment_milestones:
        if row.status != "Pending" or getdate(row.due_date) > getdate(cutoff):
            continue
        if row.sales_invoice and frappe.db.exists("Sales Invoice", row.sales_invoice):
            created.append(row.sales_invoice)
            continue
        existing = frappe.db.get_value(
            "Sales Invoice",
            {"estateflow_agreement": agreement.name, "estateflow_milestone_row": row.name, "docstatus": ["<", 2]},
            "name",
        )
        if existing:
            frappe.db.set_value("Agreement Milestone", row.name, {"sales_invoice": existing, "status": "Invoiced"})
            created.append(existing)
            continue
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = agreement.customer
        invoice.company = agreement.company
        invoice.currency = agreement.currency
        invoice.posting_date = min(getdate(nowdate()), getdate(row.due_date))
        invoice.due_date = row.due_date
        _apply_estateflow_dimensions(
            invoice, property_name=agreement.property, space=agreement.space,
            agreement=agreement.name, period_start=row.due_date, period_end=row.due_date,
            billing_source="Agreement Milestone", milestone_row=row.name,
        )
        invoice.append("items", {
            "item_code": _require_item(row.item_code, row.milestone),
            "description": row.description or row.milestone,
            "qty": 1, "rate": row.amount,
            "income_account": defaults.income_account, "cost_center": defaults.cost_center,
        })
        _insert_invoice(invoice, submit)
        frappe.db.set_value(
            "Agreement Milestone", row.name,
            {"sales_invoice": invoice.name, "status": "Invoiced", "outstanding_amount": invoice.outstanding_amount},
        )
        created.append(invoice.name)
    return created


def generate_due_agreement_invoices_for_contract(agreement_name, as_of_date=None, submit=None):
    cutoff = getdate(as_of_date or nowdate())
    created = []
    for _ in range(24):
        agreement = frappe.get_doc("Occupancy Agreement", agreement_name)
        trigger = _agreement_trigger_date(agreement)
        if not agreement.auto_generate_invoices or not trigger or trigger > cutoff:
            break
        invoice = generate_agreement_invoice(agreement.name, agreement.next_invoice_date, submit=submit)
        created.append(invoice.name)
    created.extend(generate_agreement_milestone_invoices(agreement_name, cutoff, submit=submit))
    return list(dict.fromkeys(created))


def create_reservation_invoice(reservation_name, submit=None):
    reservation = frappe.get_doc("Property Reservation", reservation_name)
    if reservation.docstatus != 1:
        frappe.throw(_("Submit the reservation before creating an invoice."))
    if reservation.sales_invoice:
        existing = frappe.get_doc("Sales Invoice", reservation.sales_invoice)
        if existing.docstatus < 2:
            return existing

    defaults = get_property_defaults(reservation.property)
    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = reservation.customer
    invoice.company = defaults.company or get_estateflow_settings().company
    invoice.currency = reservation.currency
    invoice.posting_date = nowdate()
    invoice.due_date = nowdate()
    _apply_estateflow_dimensions(
        invoice,
        property_name=reservation.property,
        space=reservation.space,
        reservation=reservation.name,
        period_start=reservation.arrival_date,
        period_end=reservation.departure_date,
        billing_source="Reservation / Stay",
    )

    space_item = frappe.db.get_value("Property Space", reservation.space, "item_code")
    default_item = (
        "ESTATEFLOW-ACCOMMODATION"
        if reservation.reservation_type == "Hotel / Lodge Stay"
        else "ESTATEFLOW-RESERVATION"
    )
    periods = reservation.number_of_nights if reservation.reservation_type == "Hotel / Lodge Stay" else 1
    invoice.append(
        "items",
        {
            "item_code": _require_item(space_item or default_item, "reservation base charge"),
            "description": _("{0}: {1} to {2}").format(
                reservation.space, reservation.arrival_date, reservation.departure_date
            ),
            "qty": periods or 1,
            "rate": reservation.base_rate,
            "income_account": defaults.income_account,
            "cost_center": defaults.cost_center,
        },
    )
    for charge in reservation.charges:
        invoice.append(
            "items",
            {
                "item_code": _require_item(charge.item_code, charge.description),
                "description": charge.description,
                "qty": charge.qty or 1,
                "rate": charge.rate,
                "income_account": charge.income_account or defaults.income_account,
                "cost_center": charge.cost_center or defaults.cost_center,
            },
        )
    if reservation.discount_amount:
        invoice.apply_discount_on = "Grand Total"
        invoice.discount_amount = reservation.discount_amount
    _insert_invoice(invoice, submit)
    reservation.db_set("sales_invoice", invoice.name)
    return invoice


def generate_sale_installment_invoices(contract_name, as_of_date=None, submit=None):
    contract = frappe.get_doc("Property Sale Contract", contract_name)
    contract.check_permission("read")
    if contract.docstatus != 1 or contract.status not in ("Active", "Completed"):
        frappe.throw(_("Only an active submitted sale contract can be billed."))

    cutoff = getdate(as_of_date or nowdate())
    defaults = get_property_defaults(contract.property)
    created = []
    for row in contract.installments:
        if row.status != "Pending" or getdate(row.due_date) > cutoff:
            continue
        existing = frappe.db.get_value(
            "Sales Invoice",
            {"estateflow_sale_contract": contract.name, "due_date": row.due_date, "docstatus": ["<", 2]},
            "name",
        )
        if existing:
            frappe.db.set_value("Sale Installment", row.name, {"sales_invoice": existing, "status": "Invoiced"})
            created.append(existing)
            continue

        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = contract.customer
        invoice.company = contract.company
        invoice.currency = contract.currency
        invoice.posting_date = min(getdate(nowdate()), getdate(row.due_date))
        invoice.due_date = row.due_date
        _apply_estateflow_dimensions(
            invoice,
            property_name=contract.property,
            space=contract.space,
            sale_contract=contract.name,
            billing_source="Property Sale Milestone",
            milestone_row=row.name,
        )
        invoice.append(
            "items",
            {
                "item_code": _require_item(row.item_code or "ESTATEFLOW-PROPERTY-SALE", row.milestone),
                "description": row.milestone,
                "qty": 1,
                "rate": row.amount,
                "income_account": defaults.income_account,
                "cost_center": defaults.cost_center,
            },
        )
        _insert_invoice(invoice, submit)
        frappe.db.set_value("Sale Installment", row.name, {"sales_invoice": invoice.name, "status": "Invoiced"})
        created.append(invoice.name)
    return created


def create_utility_invoice(reading_name, submit=None):
    reading = frappe.get_doc("Utility Reading", reading_name)
    if reading.docstatus != 1:
        frappe.throw(_("Submit the utility reading before billing it."))
    if reading.sales_invoice:
        return frappe.get_doc("Sales Invoice", reading.sales_invoice)
    if not reading.customer:
        frappe.throw(_("Select the customer to bill."))

    meter = frappe.get_doc("Utility Meter", reading.meter)
    defaults = get_property_defaults(meter.property)
    invoice = frappe.new_doc("Sales Invoice")
    invoice.customer = reading.customer
    invoice.company = defaults.company or get_estateflow_settings().company
    invoice.currency = reading.currency or meter.currency
    invoice.posting_date = reading.reading_date
    invoice.due_date = add_days(reading.reading_date, get_estateflow_settings().default_receivable_days or 0)
    _apply_estateflow_dimensions(
        invoice, property_name=meter.property, space=meter.space,
        billing_source="Utility Reading",
    )
    invoice.append(
        "items",
        {
            "item_code": _require_item(meter.item_code or "ESTATEFLOW-UTILITY", "utility billing"),
            "description": _("{0} consumption: {1}").format(meter.meter_type, reading.consumption),
            "qty": reading.consumption,
            "rate": meter.rate_per_unit,
            "income_account": defaults.income_account,
            "cost_center": defaults.cost_center,
        },
    )
    _insert_invoice(invoice, submit)
    reading.db_set("sales_invoice", invoice.name)
    return invoice


def _refresh_installment_payment_statuses():
    rows = frappe.db.sql(
        """
        select si.name, si.outstanding_amount, si.grand_total, inst.name as installment
        from `tabSale Installment` inst
        inner join `tabSales Invoice` si on si.name = inst.sales_invoice
        where inst.status in ('Invoiced', 'Partly Paid') and si.docstatus = 1
        """,
        as_dict=True,
    )
    for row in rows:
        if flt(row.outstanding_amount) <= 0:
            status = "Paid"
        elif flt(row.outstanding_amount) < flt(row.grand_total):
            status = "Partly Paid"
        else:
            status = "Invoiced"
        frappe.db.set_value(
            "Sale Installment", row.installment,
            {"status": status, "paid_amount": flt(row.grand_total) - flt(row.outstanding_amount), "outstanding_amount": row.outstanding_amount},
        )


@frappe.whitelist()
def run_daily_billing():
    if frappe.request:
        frappe.only_for(("System Manager", "EstateFlow Administrator"))
    settings = get_estateflow_settings()
    today = getdate(nowdate())

    if settings.invoice_agreements_daily:
        agreements = frappe.get_all(
            "Occupancy Agreement",
            filters={
                "docstatus": 1,
                "status": ["in", ["Pending Activation", "Active", "Notice Given"]],
                "end_date": [">=", today],
            },
            pluck="name",
            limit_page_length=1000,
        )
        for name in agreements:
            try:
                generate_due_agreement_invoices_for_contract(name, today)
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"EstateFlow agreement billing: {name}")

    if settings.invoice_sale_installments_daily:
        contracts = frappe.get_all(
            "Property Sale Contract",
            filters={"docstatus": 1, "status": "Active"},
            pluck="name",
            limit_page_length=500,
        )
        for name in contracts:
            try:
                generate_sale_installment_invoices(name, today)
            except Exception:
                frappe.log_error(frappe.get_traceback(), f"EstateFlow sale billing: {name}")

    _refresh_installment_payment_statuses()
