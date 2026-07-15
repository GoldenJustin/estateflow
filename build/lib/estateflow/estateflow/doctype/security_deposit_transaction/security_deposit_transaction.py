import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate

from estateflow.utils import get_estateflow_settings


class SecurityDepositTransaction(Document):
    def validate(self):
        self.posting_date = self.posting_date or nowdate()
        agreement = frappe.get_doc("Occupancy Agreement", self.agreement)
        if agreement.docstatus != 1:
            frappe.throw(_("Security deposits can be posted only for a submitted occupancy agreement."))
        self.company = agreement.company
        self.customer = agreement.customer
        self.property = agreement.property
        self.space = agreement.space

        company_currency = frappe.db.get_value("Company", self.company, "default_currency")
        self.currency = company_currency
        if agreement.currency != company_currency:
            frappe.throw(
                _("Automated deposit journals currently require the agreement currency to equal company currency. Post an accountant-approved multi-currency Journal Entry instead.")
            )
        if flt(self.amount) <= 0:
            frappe.throw(_("Deposit transaction amount must be greater than zero."))

        settings = get_estateflow_settings()
        self.liability_account = self.liability_account or settings.security_deposit_account
        if not self.liability_account:
            frappe.throw(_("Set the Security Deposit Liability Account in EstateFlow Settings."))
        self._validate_account(self.liability_account, expected_root="Liability")

        if self.transaction_type in ("Receipt", "Refund"):
            if not self.bank_account:
                frappe.throw(_("Select a bank or cash account."))
            self._validate_account(self.bank_account, expected_root="Asset")
        elif self.transaction_type == "Apply to Invoice":
            self._validate_invoice()
        elif self.transaction_type == "Adjustment":
            if not self.adjustment_account:
                frappe.throw(_("Select the adjustment account."))
            self._validate_account(self.adjustment_account)

        if self.transaction_type != "Receipt" and flt(self.amount) > self._available_balance():
            frappe.throw(_("This transaction exceeds the available deposit balance."))

    def before_submit(self):
        if self.journal_entry:
            frappe.throw(_("Journal Entry {0} is already linked.").format(self.journal_entry))
        journal = self._make_journal_entry()
        journal.insert()
        journal.submit()
        self.journal_entry = journal.name
        self.status = "Posted"

    def on_submit(self):
        self._update_agreement_balance()

    def before_cancel(self):
        if self.journal_entry:
            journal = frappe.get_doc("Journal Entry", self.journal_entry)
            if journal.docstatus == 1:
                journal.cancel()

    def on_cancel(self):
        self.db_set("status", "Cancelled")
        self._update_agreement_balance()

    def _validate_account(self, account, expected_root=None):
        values = frappe.db.get_value("Account", account, ["company", "root_type", "is_group"], as_dict=True)
        if not values or values.company != self.company:
            frappe.throw(_("Account {0} must belong to {1}.").format(frappe.bold(account), self.company))
        if values.is_group:
            frappe.throw(_("Account {0} cannot be a group.").format(frappe.bold(account)))
        if expected_root and values.root_type != expected_root:
            frappe.throw(_("Account {0} must be an {1} account.").format(frappe.bold(account), expected_root))

    def _validate_invoice(self):
        if not self.sales_invoice:
            frappe.throw(_("Select the Sales Invoice to settle."))
        invoice = frappe.db.get_value(
            "Sales Invoice", self.sales_invoice,
            ["company", "customer", "outstanding_amount", "docstatus", "estateflow_agreement"],
            as_dict=True,
        )
        if not invoice or invoice.docstatus != 1:
            frappe.throw(_("Select a submitted Sales Invoice."))
        if invoice.company != self.company or invoice.customer != self.customer:
            frappe.throw(_("The invoice must belong to the same company and customer."))
        if invoice.estateflow_agreement and invoice.estateflow_agreement != self.agreement:
            frappe.throw(_("The invoice is linked to a different occupancy agreement."))
        if flt(self.amount) > flt(invoice.outstanding_amount):
            frappe.throw(_("Amount cannot exceed the invoice outstanding balance."))

    def _available_balance(self):
        result = frappe.db.sql(
            """
            select coalesce(sum(case when transaction_type = 'Receipt' then amount else -amount end), 0)
            from `tabSecurity Deposit Transaction`
            where agreement = %s and docstatus = 1 and name != %s
            """,
            (self.agreement, self.name or ""),
        )
        return flt(result[0][0] if result else 0)

    def _make_journal_entry(self):
        journal = frappe.new_doc("Journal Entry")
        journal.voucher_type = "Journal Entry"
        journal.company = self.company
        journal.posting_date = self.posting_date
        journal.cheque_no = self.reference_no
        journal.cheque_date = self.posting_date if self.reference_no else None
        journal.user_remark = _("Security deposit {0} for agreement {1}").format(self.transaction_type.lower(), self.agreement)
        if journal.meta.has_field("estateflow_property"):
            journal.estateflow_property = self.property
            journal.estateflow_space = self.space
            journal.estateflow_agreement = self.agreement

        liability = {"account": self.liability_account}
        other = {}
        if self.transaction_type == "Receipt":
            other = {"account": self.bank_account, "debit_in_account_currency": self.amount}
            liability["credit_in_account_currency"] = self.amount
        elif self.transaction_type == "Refund":
            liability["debit_in_account_currency"] = self.amount
            other = {"account": self.bank_account, "credit_in_account_currency": self.amount}
        elif self.transaction_type == "Apply to Invoice":
            invoice = frappe.db.get_value("Sales Invoice", self.sales_invoice, ["debit_to"], as_dict=True)
            liability["debit_in_account_currency"] = self.amount
            other = {
                "account": invoice.debit_to,
                "party_type": "Customer",
                "party": self.customer,
                "reference_type": "Sales Invoice",
                "reference_name": self.sales_invoice,
                "credit_in_account_currency": self.amount,
            }
        else:
            liability["debit_in_account_currency"] = self.amount
            other = {"account": self.adjustment_account, "credit_in_account_currency": self.amount}

        journal.append("accounts", liability)
        journal.append("accounts", other)
        return journal

    def _update_agreement_balance(self):
        balance = frappe.db.sql(
            """
            select coalesce(sum(case when transaction_type = 'Receipt' then amount else -amount end), 0)
            from `tabSecurity Deposit Transaction`
            where agreement = %s and docstatus = 1
            """,
            self.agreement,
        )[0][0]
        frappe.db.set_value(
            "Occupancy Agreement",
            self.agreement,
            {
                "security_deposit_balance": balance,
                "security_deposit_received": 1 if flt(balance) > 0 else 0,
                "deposit_reference_doctype": "Security Deposit Transaction",
                "deposit_reference": self.name,
            },
        )
