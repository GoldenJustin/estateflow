"""Configurable, deduplicated EstateFlow email notifications."""

from __future__ import annotations

import frappe
from frappe import _
from frappe.utils import add_days, cint, getdate, now_datetime, nowdate

from estateflow.utils import get_estateflow_settings


def _days(value, fallback):
    try:
        return sorted({cint(part.strip()) for part in (value or fallback).split(",") if part.strip()}, reverse=True)
    except Exception:
        return [cint(x) for x in fallback.split(",")]


def _customer_emails(customer):
    if not customer:
        return []
    emails = frappe.db.sql(
        """
        select distinct c.email_id
        from `tabContact` c
        inner join `tabDynamic Link` dl on dl.parent = c.name and dl.parenttype = 'Contact'
        where dl.link_doctype = 'Customer' and dl.link_name = %s
          and coalesce(c.email_id, '') != ''
        order by c.is_primary_contact desc, c.modified desc
        """,
        customer,
    )
    values = [row[0] for row in emails if row[0]]
    if not values and frappe.get_meta("Customer").has_field("email_id"):
        email = frappe.db.get_value("Customer", customer, "email_id")
        if email:
            values.append(email)
    return list(dict.fromkeys(values))


def _property_manager_email(property_name):
    if not property_name:
        return None
    user = frappe.db.get_value("Real Estate Property", property_name, "property_manager")
    return frappe.db.get_value("User", user, "email") if user else None


def _render(template_name, context, default_subject, default_message):
    if template_name and frappe.db.exists("Email Template", template_name):
        template = frappe.get_doc("Email Template", template_name)
        return (
            frappe.render_template(template.subject or default_subject, context),
            frappe.render_template(template.response or default_message, context),
        )
    return frappe.render_template(default_subject, context), frappe.render_template(default_message, context)


def _sender(settings):
    if not settings.notification_sender:
        return None
    return frappe.db.get_value("Email Account", settings.notification_sender, "email_id")


def send_event(*, event_key, event_type, reference_doctype, reference_name, recipients,
               subject, message, property_name=None):
    settings = get_estateflow_settings()
    if not settings.enable_email_notifications:
        return []
    recipients = list(dict.fromkeys([email for email in recipients if email]))
    if settings.copy_property_manager:
        manager = _property_manager_email(property_name)
        if manager and manager not in recipients:
            recipients.append(manager)
    sent = []
    for recipient in recipients:
        key = f"{event_key}:{recipient}"[:140]
        if frappe.db.exists("EstateFlow Notification Log", {"event_key": key}):
            continue
        log = frappe.get_doc({
            "doctype": "EstateFlow Notification Log", "event_key": key, "event_type": event_type,
            "reference_doctype": reference_doctype, "reference_name": reference_name,
            "recipient": recipient, "subject": subject, "status": "Queued", "sent_on": now_datetime(),
        }).insert(ignore_permissions=True)
        try:
            frappe.sendmail(
                recipients=[recipient], sender=_sender(settings), subject=subject, message=message,
                reference_doctype=reference_doctype, reference_name=reference_name, now=False,
            )
            sent.append(log.name)
        except Exception as exc:
            frappe.db.set_value("EstateFlow Notification Log", log.name, {"status": "Failed", "error": str(exc)[:500]})
            frappe.log_error(frappe.get_traceback(), f"EstateFlow email: {event_type} {reference_name}")
    return sent


def notify_contract_activation(agreement):
    settings = get_estateflow_settings()
    if not settings.send_contract_activation_email:
        return
    context = {"doc": agreement, "customer": agreement.customer, "property": agreement.property, "space": agreement.space}
    subject, message = _render(
        settings.activation_email_template, context,
        _("Occupancy agreement {{ doc.name }} is now active"),
        _("<p>Hello {{ customer }},</p><p>Your occupancy agreement for <b>{{ property }} / {{ space }}</b> is active from {{ doc.start_date }} to {{ doc.end_date }}.</p>"),
    )
    send_event(event_key=f"activation:{agreement.name}", event_type="Contract Activated", reference_doctype=agreement.doctype,
               reference_name=agreement.name, recipients=_customer_emails(agreement.customer), subject=subject, message=message,
               property_name=agreement.property)


def notify_contract_expired(agreement):
    settings = get_estateflow_settings()
    if not settings.send_contract_expired_email:
        return
    context = {"doc": agreement, "customer": agreement.customer, "property": agreement.property, "space": agreement.space}
    subject, message = _render(
        settings.contract_expired_email_template, context,
        _("Occupancy agreement {{ doc.name }} has expired"),
        _("<p>The occupancy agreement for <b>{{ property }} / {{ space }}</b> ended on {{ doc.end_date }}.</p>"),
    )
    send_event(event_key=f"expired:{agreement.name}", event_type="Contract Expired", reference_doctype=agreement.doctype,
               reference_name=agreement.name, recipients=_customer_emails(agreement.customer), subject=subject, message=message,
               property_name=agreement.property)


def send_invoice_issued(invoice):
    settings = get_estateflow_settings()
    if not settings.send_invoice_email or invoice.docstatus != 1 or not invoice.get("estateflow_property"):
        return
    context = {"doc": invoice, "customer": invoice.customer, "property": invoice.get("estateflow_property")}
    subject, message = _render(
        settings.invoice_email_template, context,
        _("Invoice {{ doc.name }} issued"),
        _("<p>Hello {{ customer }},</p><p>Invoice <b>{{ doc.name }}</b> for {{ doc.grand_total }} {{ doc.currency }} is due on {{ doc.due_date }}.</p>"),
    )
    send_event(event_key=f"invoice:{invoice.name}", event_type="Invoice Issued", reference_doctype=invoice.doctype,
               reference_name=invoice.name, recipients=_customer_emails(invoice.customer), subject=subject, message=message,
               property_name=invoice.get("estateflow_property"))


def send_payment_receipt(payment):
    settings = get_estateflow_settings()
    if not settings.send_payment_receipt_email or payment.docstatus != 1 or payment.party_type != "Customer":
        return
    property_name = payment.get("estateflow_property")
    invoice_names = [r.reference_name for r in payment.references if r.reference_doctype == "Sales Invoice"]
    if not property_name and invoice_names:
        property_name = frappe.db.get_value("Sales Invoice", invoice_names[0], "estateflow_property")
    if not property_name:
        return
    context = {"doc": payment, "customer": payment.party, "invoices": ", ".join(invoice_names), "property": property_name}
    subject, message = _render(
        settings.payment_receipt_email_template, context,
        _("Payment receipt {{ doc.name }}"),
        _("<p>Hello {{ customer }},</p><p>We received payment <b>{{ doc.name }}</b> amounting to {{ doc.paid_amount }} {{ doc.paid_from_account_currency }} for {{ invoices }}.</p>"),
    )
    send_event(event_key=f"payment:{payment.name}", event_type="Payment Receipt", reference_doctype=payment.doctype,
               reference_name=payment.name, recipients=_customer_emails(payment.party), subject=subject, message=message,
               property_name=property_name)


def send_reservation_confirmation(reservation):
    settings = get_estateflow_settings()
    if not settings.send_reservation_confirmation_email:
        return
    context = {"doc": reservation, "customer": reservation.customer, "property": reservation.property, "space": reservation.space}
    subject, message = _render(
        settings.reservation_email_template, context,
        _("Reservation {{ doc.name }} confirmed"),
        _("<p>Your reservation at <b>{{ property }}</b>, {{ space }}, is confirmed from {{ doc.arrival_date }} to {{ doc.departure_date }}.</p>"),
    )
    send_event(event_key=f"reservation:{reservation.name}", event_type="Reservation Confirmed", reference_doctype=reservation.doctype,
               reference_name=reservation.name, recipients=_customer_emails(reservation.customer), subject=subject, message=message,
               property_name=reservation.property)


@frappe.whitelist()
def run_daily_notifications():
    if frappe.request:
        frappe.only_for(("System Manager", "EstateFlow Administrator"))
    settings = get_estateflow_settings()
    if not settings.enable_email_notifications:
        return
    today = getdate(nowdate())
    if settings.send_contract_expiry_alerts:
        for days in _days(settings.contract_expiry_reminder_days, "90,60,30,14,7,1"):
            target = add_days(today, days)
            agreements = frappe.get_all(
                "Occupancy Agreement",
                filters={"docstatus": 1, "status": ["in", ["Active", "Notice Given"]], "end_date": target},
                fields=["name", "customer", "property", "space", "start_date", "end_date"],
            )
            for agreement in agreements:
                context = {"doc": agreement, "days": days, "customer": agreement.customer, "property": agreement.property, "space": agreement.space}
                subject, message = _render(
                    settings.expiry_email_template, context,
                    _("Agreement {{ doc.name }} expires in {{ days }} day(s)"),
                    _("<p>Your agreement for <b>{{ property }} / {{ space }}</b> expires on {{ doc.end_date }} ({{ days }} day(s)).</p>"),
                )
                send_event(event_key=f"expiry:{agreement.name}:{days}", event_type="Contract Expiry Reminder",
                           reference_doctype="Occupancy Agreement", reference_name=agreement.name,
                           recipients=_customer_emails(agreement.customer), subject=subject, message=message,
                           property_name=agreement.property)
    if settings.send_overdue_reminders:
        for days in _days(settings.overdue_reminder_days, "1,7,14,30"):
            due_date = add_days(today, -days)
            invoices = frappe.get_all(
                "Sales Invoice",
                filters={"docstatus": 1, "due_date": due_date, "outstanding_amount": [">", 0], "estateflow_property": ["is", "set"]},
                fields=["name", "customer", "estateflow_property", "grand_total", "outstanding_amount", "currency", "due_date"],
            )
            for invoice in invoices:
                context = {"doc": invoice, "days": days, "customer": invoice.customer, "property": invoice.estateflow_property}
                subject, message = _render(
                    settings.overdue_email_template, context,
                    _("Invoice {{ doc.name }} is overdue"),
                    _("<p>Invoice <b>{{ doc.name }}</b> has {{ doc.outstanding_amount }} {{ doc.currency }} outstanding and is {{ days }} day(s) overdue.</p>"),
                )
                send_event(event_key=f"overdue:{invoice.name}:{days}", event_type="Overdue Reminder",
                           reference_doctype="Sales Invoice", reference_name=invoice.name,
                           recipients=_customer_emails(invoice.customer), subject=subject, message=message,
                           property_name=invoice.estateflow_property)
