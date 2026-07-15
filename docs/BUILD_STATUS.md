# EstateFlow build status

Updated: 2026-07-15 · Version: 0.1.4

## Delivered in this milestone

- [x] Installable Frappe app package and hooks
- [x] ERPNext dependency check
- [x] Upgrade-safe Custom Fields on Accounts, Buying and Stock documents
- [x] Nine EstateFlow roles
- [x] Single settings DocType with eight business-mode switches
- [x] Guided first-run setup and safe standard service Items
- [x] Universal portfolio/property/space hierarchy
- [x] Occupancy and housekeeping state model
- [x] Property listings, enquiries, viewings and offers
- [x] Hotel/lodge and generic reservation flow
- [x] Date/capacity validation and cross-document availability engine
- [x] Confirm, check-in, invoice and check-out actions
- [x] Long-term occupancy agreement and recurring charges
- [x] Security-deposit receipt/refund/application/adjustment Journal Entries and balance
- [x] Scheduled agreement invoicing with duplicate protection
- [x] Property sale contract and installment billing
- [x] Agent commission payable flow
- [x] Housing application and property allocation
- [x] Allocation conversion to tenancy or sale
- [x] Maintenance request, SLA and work order
- [x] Work Order to Material Request handoff
- [x] Property inspection and issue generation
- [x] Utility meters, consumption and customer invoice
- [x] Responsive Command Center with live aggregates
- [x] In-app operating manual with live setup checklist and ten business playbooks
- [x] Guided setup result summary explaining every change and next step
- [x] Permanent Frappe Docker custom-image manifest and deployment guide
- [x] Availability Register, Rent Roll and Lease Expiry reports
- [x] Customer self-service summary portal
- [x] Daily expiry and billing schedulers
- [x] README product/technical presentation
- [x] Static schema test suite

## Requires a Frappe bench before release tagging

- [ ] Install/migrate smoke test on a clean ERPNext 15 site
- [ ] Install/migrate smoke test on a clean ERPNext 16 site
- [ ] End-to-end submitted Sales Invoice and Payment Entry test
- [ ] End-to-end Material Request → Purchase Order → Purchase Receipt → Purchase Invoice test
- [ ] Permission matrix test for each custom role
- [ ] Multi-company and mixed-currency test
- [ ] Cancellation/amendment test for every submittable document
- [ ] Scheduler idempotency under concurrent workers
- [ ] Print-format and translation review
- [ ] Accessibility and mobile-device QA

## Deliberately not automated without local policy

The following need implementation/configuration approved by the deploying organization:

- Tax/VAT and withholding rules
- Security-deposit custody, deduction approval, multi-currency and refund policy
- Owner trust accounting and disbursement policy
- Government-housing eligibility formula
- Property sale revenue-recognition policy
- Local fiscal-device/e-invoice integration
- KYC/identity-provider integration
- Online payments, e-signature, SMS and WhatsApp

## Next development order

1. Bench compatibility and integration test pass
2. Owner accounting and service-charge reconciliation
3. Hotel rate plan/room move/package layer
4. Preventive maintenance generator and asset/QR layer
5. Visual inventory stack plan and map
6. Localization package selected by deployment country
