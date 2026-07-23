# EstateFlow Client Demonstration and UAT Manual

## Purpose

Use one controlled demonstration and UAT run per client business case. Do not present only screens: demonstrate inventory state, operational status, accounting result, email/log result and report reconciliation.

## Demonstration preparation

1. Create a separate test company or staging site.
2. Configure company currency, cost centre, income, expense and deposit-liability accounts.
3. Run EstateFlow Guided Setup and enable only the client's initial modes.
4. Configure an outgoing Email Account before enabling EstateFlow emails.
5. Create test Customers, Suppliers, Items, warehouses and users—never use production identities.
6. Create an **EstateFlow UAT Run** for the selected business case. It loads the full template automatically.
7. Record evidence and actual result for every case. Submit only when all cases are tested or marked Not Applicable.

## Standard client presentation order

1. **Guide & Setup** — explain what setup creates and what remains client data.
2. **Portfolio** — explain owner/program/fund/group reporting boundary.
3. **Property and Space** — demonstrate the universal inventory model.
4. **Primary business transaction** — lease, booking, sale, allocation or work order.
5. **Automated lifecycle** — activation, billing, reminders and expiry.
6. **Accounting** — Sales Invoice/Purchase Invoice, Payment Entry, Journal Entry and Contract Billing Event.
7. **Public experience** — `/properties` and `/my-estate` where relevant.
8. **Reports** — reconcile operations to accounting.
9. **UAT Run** — record pass/fail, evidence and client sign-off.

## Demonstration scripts

### Individual landlord

Create one residential Property with one rentable house Space. Create a tenant and future Occupancy Agreement. Show Pending Activation, activate it, generate the first invoice, receive deposit, collect payment, raise a maintenance request and expire the contract. Reconcile Rent Roll, Contract Billing Tracker, receivables and property P&L.

### Hotel or lodge

Create one Hotel/Lodge Property and at least three bookable rooms: Clean/Available, Occupied and Dirty. Show public listing, availability, overlap prevention, confirmation email, check-in, folio invoice, payment receipt, checkout and housekeeping. Reconcile Hotel Operations and Billing Tracker.

### Property agency

Publish an owner listing with image, then demonstrate enquiry → viewing → offer → reservation hold → lease/sale → commission Purchase Invoice. Show expiry removal from `/properties` and Sales Pipeline reporting.

### National/social housing

Create scheme, allocatable units and applicant. Demonstrate application evidence, review/waitlist, approved allocation, duplicate-allocation prevention and conversion to tenancy or purchase. Reconcile Housing Allocation Register, Billing Tracker and arrears.

### Developer sales

Create sellable unit, reserve it, create contract with multiple installments, reject an invalid schedule, issue due milestone invoices, record partial/full payment and complete handover. Reconcile sale installments and Billing Tracker.

### Property management

Create managed portfolio with multiple properties and owners. Demonstrate lease automation, arrears, inspection, utility billing and request-to-procurement. Reconcile Portfolio Performance, Maintenance SLA and ERPNext accounting.

### Commercial/retail/warehouse

Create shop/office/warehouse Spaces and a multi-charge agreement with rent, service charge and parking. Demonstrate advance quarterly billing, utility rebilling, expiry alerts and facilities cost. Reconcile Rent Roll and Portfolio Performance.

### HOA/community

Create home and common-area Spaces. Demonstrate recurring HOA Levy, arrears reminders and common-property work order. Explicitly identify planned features such as meetings/voting if requested.

### Investment portfolio/REIT foundation

Create multiple assets with cost centres/projects. Demonstrate linked income and expense, occupancy, collections and operating margin. Explicitly identify valuation, investor registry and distribution waterfall as controlled extensions.

### Facilities and maintenance

Demonstrate priority/SLA, assignment, inspection finding, material request, buying chain, completion and housekeeping turnover. Reconcile Maintenance SLA and linked Purchase documents.

## Required report reconciliation

| Report | Must reconcile to |
|---|---|
| Command Center | Property/Space status, Sales Invoice and Maintenance Request |
| Availability Register | Property Space plus blocking reservations/agreements |
| Rent Roll | Submitted current Occupancy Agreements and Agreement Charges |
| Lease Expiry | Agreement end date/status |
| Contract Billing Tracker | Linked Sales Invoice totals and outstanding amount |
| Portfolio Performance | Property inventory, Sales Invoice and Purchase Invoice |
| Hotel Operations | Reservations, room housekeeping and folio invoices |
| Maintenance SLA | Maintenance Request status and due timestamps |
| Real Estate Sales Pipeline | Enquiry, Viewing Appointment and Property Offer |
| Housing Allocation Register | Application/allocation/agreement/sale links |
| EstateFlow UAT Summary | UAT Run result rows and evidence |

## Acceptance gates

- No duplicate invoices after rerunning schedulers.
- No double booking/allocation for overlapping dates.
- Every property invoice has an EstateFlow reference and Billing Event.
- Payment/cancellation updates outstanding and milestone status.
- Emails are deduplicated and logged.
- Roles cannot bypass accounting or company restrictions.
- Reports reconcile to source documents and GL.
- Frontend remains usable on mobile and keyboard navigation.
- Background workers and scheduler remain healthy throughout testing.
