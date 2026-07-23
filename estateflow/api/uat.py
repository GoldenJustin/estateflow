"""Client-facing UAT templates for every supported EstateFlow business case."""

from __future__ import annotations

import frappe
from frappe import _


def case(test_id, module, scenario, steps, expected, accounting="", severity="High", preconditions="Configured company and test user"):
    return {
        "test_id": test_id, "module": module, "scenario": scenario, "preconditions": preconditions,
        "test_steps": steps, "expected_result": expected, "accounting_result": accounting,
        "severity": severity, "status": "Not Tested",
    }


COMMON = [
    case("COM-001", "Setup", "Run setup twice without duplicates", "Run Guided Setup with modes and service Items; run it again.", "Settings update, one portfolio remains, and standard Items are not duplicated.", severity="Critical"),
    case("COM-002", "Security", "Role and company access", "Login as each operational role and attempt permitted and restricted records.", "Users see only authorized companies/properties and cannot submit accounting documents without standard ERPNext roles.", severity="Critical"),
    case("COM-003", "Accounting", "Manual invoice connection", "Create a Sales Invoice, set EstateFlow Property and Agreement, then submit.", "Sales Invoice appears in agreement connections and creates/updates one Contract Billing Event.", "Receivable and configured income are posted once.", "Critical"),
    case("COM-004", "Accounting", "Payment receipt and tracking", "Submit Payment Entry against the linked invoice.", "Invoice outstanding, Billing Event paid/outstanding, milestone status and agreement connection refresh.", "Bank/Cash debited and Receivable credited.", "Critical"),
    case("COM-005", "Notifications", "Email deduplication", "Enable emails and trigger the same invoice/payment/expiry event twice.", "One email per recipient/event key; Notification Log shows queued/sent/skipped/failed state.", severity="High"),
    case("COM-006", "Audit", "Cancellation and amendment", "Cancel a linked invoice or contract and amend it.", "Statuses, inventory and Billing Event reflect cancellation without duplicate active obligations.", "Cancelled GL entries reverse according to ERPNext.", "Critical"),
    case("COM-007", "Reporting", "Report drill-down", "Open dashboard KPI and relevant reports; drill into source documents.", "Totals agree with source documents and filters for company/portfolio/property/date.", severity="High"),
]


TEMPLATES = {
    "Individual Landlord": [
        case("LL-001", "Inventory", "Single house setup", "Create portfolio, residential property and one rentable house Space.", "Space is Available, rentable and visible in Availability Register."),
        case("LL-002", "Contract", "Future lease activation", "Submit agreement with future start date.", "Status is Pending Activation and space is Reserved; daily job activates it on start date."),
        case("LL-003", "Billing", "First rent on activation", "Enable first invoice on activation and activate agreement.", "One invoice is created with agreement/property/space and first billing period; no duplicate on rerun.", "Dr Receivable / Cr Rent Income", "Critical"),
        case("LL-004", "Billing", "Recurring monthly rent", "Advance scheduler to next billing trigger.", "Next invoice is created according to trigger and next_invoice_date advances exactly one period.", "One receivable/income posting per period", "Critical"),
        case("LL-005", "Deposit", "Receive, apply and refund deposit", "Post receipt; apply part to invoice; refund balance.", "Agreement deposit balance and linked Journal Entries reconcile to zero.", "Bank, liability and receivable entries balance", "Critical"),
        case("LL-006", "Contract", "Automatic expiry", "Pass agreement end date and run daily operations.", "Agreement expires, tenant notification is logged, and unused space becomes Available."),
        case("LL-007", "Maintenance", "Tenant maintenance request", "Create request, work order, materials and completion.", "SLA, work status, procurement links and resolution are visible end to end."),
        case("LL-008", "Reporting", "Landlord month end", "Review Rent Roll, Billing Tracker, receivables and property P&L.", "Agreement, invoices, collections and expense totals reconcile."),
    ],
    "Hotel / Lodge": [
        case("HT-001", "Inventory", "Hotel room readiness", "Create Hotel property and bookable room with rate/capacity/Clean status.", "Room appears on availability and public listing when published."),
        case("HT-002", "Reservation", "Double-booking prevention", "Confirm one stay, then create overlapping stay for same room.", "Second reservation is blocked with the conflicting reservation and dates.", severity="Critical"),
        case("HT-003", "Reservation", "Back-to-back stays", "Create next arrival on previous departure date.", "Reservation is accepted because checkout date is exclusive."),
        case("HT-004", "Front Desk", "Check-in", "Confirm and check in guest.", "Reservation shows Checked In and room becomes Occupied with current guest."),
        case("HT-005", "Folio", "Night and extra charges", "Add nights, meal/laundry/transport charges and create invoice.", "Invoice total equals room nights plus extras less discount and links to reservation/property/room.", "Dr Receivable / Cr Accommodation and service income", "Critical"),
        case("HT-006", "Payment", "Guest payment", "Submit payment against folio invoice.", "Invoice and Billing Event become Paid and receipt email is logged."),
        case("HT-007", "Front Desk", "Checkout and housekeeping", "Check out; create and complete housekeeping work order.", "Room becomes Available/Dirty at checkout and Clean after work completion."),
        case("HT-008", "Reporting", "Daily hotel operations", "Review arrivals, departures, in-house guests, availability and room revenue.", "Operational report totals match reservations and invoices."),
    ],
    "Property Management": [
        case("PM-001", "Portfolio", "Multiple owners and properties", "Create managed portfolio, owner Customers and multiple properties/spaces.", "Portfolio groups assets and filters dashboard/performance reporting."),
        case("PM-002", "Accounting", "Property dimensions", "Post rent invoice and maintenance Purchase Invoice for one property.", "Both carry property/space references and correct cost centre/project."),
        case("PM-003", "Lease", "Lease lifecycle", "Create future lease; activate, bill, renew/notice and expire.", "Every status transition and inventory state is auditable."),
        case("PM-004", "Arrears", "Overdue collection", "Leave invoice unpaid past configured reminder days.", "Dashboard arrears and Billing Tracker show Overdue; deduplicated reminder is queued."),
        case("PM-005", "Facilities", "Request to supplier payment", "Request → Work Order → Material Request → PO → Receipt → Purchase Invoice.", "Every buying document carries property/work-order links."),
        case("PM-006", "Inspection", "Move-out inspection", "Record checklist failures and generate maintenance requests.", "Score calculates and each flagged item creates one open request."),
        case("PM-007", "Utilities", "Meter billing", "Submit sequential reading and create invoice.", "Consumption, amount, customer and invoice are correct; decreasing reading is rejected."),
        case("PM-008", "Reporting", "Portfolio performance", "Compare properties for occupancy, billing, collection, expense and NOI.", "Portfolio report reconciles with GL and operational records."),
    ],
    "Agency / Brokerage": [
        case("AG-001", "Listing", "Publish property", "Create active listing with image and publish flag.", "Card appears at /properties and detail page displays image, price and contact."),
        case("AG-002", "CRM", "Lead-to-viewing", "Capture enquiry and schedule viewing with agent.", "Source, assignment, appointment and feedback remain linked."),
        case("AG-003", "Offer", "Offer acceptance and hold", "Submit/accept offer and create reservation hold.", "Space becomes Reserved and a second conflicting hold is blocked."),
        case("AG-004", "Rental Closing", "Rental conversion", "Convert accepted rental path to occupancy agreement.", "Tenant, property, agent and commercial terms carry forward."),
        case("AG-005", "Sale Closing", "Sale contract", "Create buyer contract with installment plan.", "Contract value equals installments and space becomes Under Contract."),
        case("AG-006", "Commission", "Agent payable", "Approve supplier-agent commission and create Purchase Invoice.", "Commission payable links to deal/property and posts once.", "Dr Commission Expense / Cr Supplier Payable", "Critical"),
        case("AG-007", "Website", "Expired listing", "Pass valid-until date and run daily operations.", "Listing status becomes Expired and disappears from public portal."),
        case("AG-008", "Reporting", "Agent funnel", "Review listing, enquiry, viewing, offer, closing and commission reports.", "Counts and values reconcile by assigned agent and status."),
    ],
    "National / Social Housing": [
        case("NH-001", "Scheme", "Housing inventory", "Create scheme and allocatable rental/purchase units or plots.", "Inventory reports available, reserved, occupied and sold accurately."),
        case("NH-002", "Application", "Applicant registration", "Capture identity, household, income, needs and supporting evidence.", "Complete application is searchable and auditable without automatic policy assumptions."),
        case("NH-003", "Eligibility", "Review and waitlist", "Set eligibility result, score and reviewer; move to waitlist.", "Decision and review trail are retained."),
        case("NH-004", "Allocation", "Prevent duplicate allocation", "Approve one allocation and attempt overlapping second allocation.", "Space is Reserved and second allocation is blocked."),
        case("NH-005", "Rental", "Convert allocation to tenancy", "Create occupancy agreement from rental allocation.", "Customer/unit/dates/amount transfer and recurring billing is available."),
        case("NH-006", "Purchase", "Convert allocation to sale", "Create sale contract from purchase allocation.", "Buyer, unit and full-price installment are created and linked."),
        case("NH-007", "Collection", "Subsidized installment tracking", "Invoice and partly pay housing installment.", "Billing Event and installment show Partly Paid with exact balance."),
        case("NH-008", "Reporting", "Housing program report", "Review applications by status, allocations, occupancy, sales and arrears.", "Program totals reconcile by scheme and date."),
    ],
    "Developer Sales": [
        case("DV-001", "Inventory", "Development unit register", "Create sellable apartments/plots with prices.", "Availability shows sellable inventory and prevents sale of sold unit."),
        case("DV-002", "Reservation", "Unit reservation", "Hold unit for buyer with expiry.", "Unit is Reserved and automatically released after unconfirmed hold expiry."),
        case("DV-003", "Contract", "Installment validation", "Create contract whose installments do not equal value, then correct it.", "Invalid plan is blocked; corrected 100% plan saves/submits."),
        case("DV-004", "Billing", "Milestone invoices", "Run billing before and on installment due dates.", "Only due milestones create invoices and rerun creates no duplicates.", "Dr Buyer Receivable / Cr configured sale account", "Critical"),
        case("DV-005", "Collection", "Partial and full payment", "Part-pay then settle installment invoice.", "Installment moves Invoiced → Partly Paid → Paid with correct amounts."),
        case("DV-006", "Sale", "Sale subject to tenancy", "Sell occupied unit with and without explicit subject-to-tenancy option.", "Sale is blocked without consent option and allowed when explicitly selected."),
        case("DV-007", "Handover", "Complete sale", "Attempt completion before payment, then after all paid.", "Early completion blocked; paid contract completes and space becomes Sold."),
        case("DV-008", "Reporting", "Development sales report", "Review inventory, reservations, contracts, due installments, collections and commissions.", "Values reconcile by development and sales status."),
    ],
    "Commercial / Retail / Warehouse": [
        case("CR-001", "Inventory", "Commercial space register", "Create shops/offices/warehouses with area, zone and rent.", "Space register filters by property/type/occupancy."),
        case("CR-002", "Lease", "Multi-charge commercial lease", "Add rent, service charge, parking and insurance rows.", "Invoice contains separate Items/accounts and exact recurring total."),
        case("CR-003", "Billing", "Quarterly advance billing", "Set quarterly frequency and days-before trigger.", "Invoice is issued at lead date for correct three-month period."),
        case("CR-004", "Escalation", "Rent escalation visibility", "Configure escalation and next escalation date.", "Terms remain recorded and due escalation is visible for controlled review."),
        case("CR-005", "Utility", "Tenant utility rebilling", "Record meter reading and bill tenant.", "Usage invoice links property/unit/customer."),
        case("CR-006", "Facilities", "Common-area work", "Raise common-area request and procure service/material.", "Costs post to commercial property/cost centre."),
        case("CR-007", "Expiry", "Notice and renewal pipeline", "Review 90-day expiry report and send reminder.", "Agreement appears once at configured reminder thresholds."),
        case("CR-008", "Reporting", "Commercial rent roll", "Compare area, recurring revenue, occupancy, arrears and expiries.", "Report reconciles with agreements and invoices."),
    ],
    "HOA / Community": [
        case("HOA-001", "Community", "Homes and common areas", "Create Community property, home Spaces and Common Area Spaces.", "Community inventory distinguishes private and common spaces."),
        case("HOA-002", "Owners", "Owner and occupant register", "Link Customer/Contact and occupancy agreement to each home.", "Current occupant and agreement are visible from the Space."),
        case("HOA-003", "Levies", "Recurring HOA levy", "Add HOA Levy charge and run monthly billing.", "One invoice per period with correct property/home link."),
        case("HOA-004", "Arrears", "Levy arrears", "Leave levy unpaid and run overdue notifications.", "Outstanding and reminder logs are accurate and deduplicated."),
        case("HOA-005", "Maintenance", "Common facility issue", "Inspect common area, create request/work order and supplier bill.", "Work and cost link to common area/community."),
        case("HOA-006", "Utilities", "Shared meter", "Create shared meter and readings.", "Consumption is recorded; approved allocation policy remains explicit/manual where needed."),
        case("HOA-007", "Reporting", "Community financial view", "Review levy billing, collections, expenses and open work.", "Totals reconcile by community property."),
    ],
    "Investment Portfolio / REIT": [
        case("INV-001", "Portfolio", "Investment portfolio structure", "Create fund portfolio and multiple income properties with dimensions.", "Portfolio Performance groups every asset correctly."),
        case("INV-002", "Income", "Property income tracking", "Create and pay leases/reservations across properties.", "Revenue and collection are filterable by property/cost centre/project."),
        case("INV-003", "Expense", "Property expense tracking", "Post linked maintenance and supplier invoices.", "Expenses appear against correct asset and supplier."),
        case("INV-004", "Occupancy", "Portfolio occupancy", "Mix available, reserved, occupied and sold spaces.", "Occupancy denominator and status counts are correct."),
        case("INV-005", "NOI", "Operating performance", "Run Portfolio Performance for a date range.", "Billed income minus linked purchase expense equals report NOI definition."),
        case("INV-006", "Audit", "Drill to ledger", "Drill from portfolio to property, invoice and GL.", "Every total has source documents and no orphan operational revenue."),
        case("INV-007", "Disclosure", "Feature boundary", "Review advanced valuation/distribution needs.", "Client acknowledges valuation and regulated investor/distribution functions require approved extension."),
    ],
    "Facilities and Maintenance": [
        case("FM-001", "Request", "Priority and SLA", "Create Low, Medium, High and Emergency requests.", "SLA due dates follow configured priority multipliers."),
        case("FM-002", "Assignment", "Internal and supplier work", "Create work orders for technician and contractor.", "At least one assignee is required and schedule validates."),
        case("FM-003", "Materials", "Material request", "Add stock Items and create Material Request.", "Quantities, warehouse, property and work-order references copy correctly."),
        case("FM-004", "Procurement", "End-to-end buying", "RFQ → quotation → PO → receipt → Purchase Invoice → payment.", "Supply-chain documents remain connected to property/work order."),
        case("FM-005", "Inspection", "Failed checklist", "Submit inspection with failed maintenance flags.", "Score calculates and requests are created without duplicates."),
        case("FM-006", "Housekeeping", "Room turnover", "Complete checkout and housekeeping work order.", "Room changes Dirty → Clean and is operationally ready."),
        case("FM-007", "Completion", "Resolution control", "Attempt resolve without notes, then complete with notes.", "Missing resolution is blocked; completion updates request and actual dates."),
        case("FM-008", "Reporting", "SLA and cost", "Run Maintenance SLA report by property, priority and contractor.", "Open, overdue, completion time and linked purchasing cost reconcile."),
    ],
}


def get_cases(business_case):
    if business_case == "Complete Suite":
        cases = list(COMMON)
        for rows in TEMPLATES.values():
            cases.extend(rows)
        return cases
    return list(COMMON) + list(TEMPLATES.get(business_case, []))


@frappe.whitelist()
def preview_test_template(business_case):
    return get_cases(business_case)
