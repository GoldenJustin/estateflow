# EstateFlow 0.2.0 release notes

## Contract and billing automation

- Future agreements submit as Pending Activation and reserve the space.
- Daily lifecycle activates contracts on start date and expires them after end date.
- Per-agreement invoice trigger: On Activation, On Period Start, or Days Before Period Start.
- Recurring charges and dated one-time Agreement Milestones.
- Catch-up billing and duplicate guards by agreement/period/milestone.
- Contract Billing Event ledger for draft, unpaid, overdue, partly paid, paid and cancelled invoices.
- Payment Entry updates Billing Event and milestone paid/outstanding amounts.
- Existing manually created property invoices can be rebuilt into the billing ledger.

## Email configuration

- Activation, expiry reminder, expired, invoice, payment receipt, overdue and reservation messages.
- Seven editable default Email Templates created by Guided Setup/migration.
- Configurable reminder-day lists and optional Property Manager copy.
- Deduplicated EstateFlow Notification Log.
- Global switch remains disabled after migration until an administrator confirms the outgoing Email Account.

## Property marketing

- Public `/properties` marketplace and responsive listing detail page.
- Publish flag, public route, featured-image fallback and public contact fields.
- Activate/Publish and View Public Listing actions.

## Portfolio and reporting

- Portfolio filter on Command Center.
- Portfolio currency, target occupancy and cost centre.
- Portfolio Performance, Contract Billing Tracker, Hotel Operations, Maintenance SLA, Real Estate Sales Pipeline, Housing Allocation Register and EstateFlow UAT Summary reports.

## Client testing

- In-app EstateFlow Test Center.
- EstateFlow UAT Run and UAT Result records with evidence, severity, issue reference and client sign-off.
- Ten business templates plus common security/accounting/reporting tests.
- Excel workbook at `docs/EstateFlow_UAT_Testing_Template.xlsx`.
- Client demonstration manual at `docs/CLIENT_DEMO_AND_UAT.md`.

## Upgrade procedure

```bash
cd /home/frappe/frappe-bench/apps/estateflow
git pull upstream main
cd /home/frappe/frappe-bench
bench --site your-site migrate
bench --site your-site clear-cache
bench --site your-site clear-website-cache
```

Then open EstateFlow Settings, review Contract Automation and Email Notifications, run **Rebuild Billing Tracker**, and execute a staging UAT Run before production billing.
