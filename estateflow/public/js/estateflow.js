/* Contextual actions keep each EstateFlow process self-explanatory. */
(() => {
    const open_doc = (doctype, name) => name && frappe.set_route("Form", doctype, name);
    const run_doc_method = async (frm, method, args = {}, message = null) => {
        frappe.dom.freeze(message || __("Working…"));
        try {
            const response = await frm.call(method, args);
            await frm.reload_doc();
            return response.message;
        } finally {
            frappe.dom.unfreeze();
        }
    };
    const property_space_query = (frm, extra = {}) => {
        frm.set_query("space", () => ({ filters: Object.assign({ property: frm.doc.property }, extra) }));
    };

    frappe.ui.form.on("Real Estate Property", {
        refresh(frm) {
            frm.add_custom_button(__("Add Unit / Room / Space"), () => frappe.new_doc("Property Space", { property: frm.doc.name }));
            frm.add_custom_button(__("Availability"), () => frappe.set_route("query-report", "Availability Register", { property: frm.doc.name }));
        },
    });

    frappe.ui.form.on("Property Reservation", {
        setup(frm) { property_space_query(frm, { status: "Ready" }); },
        property(frm) { property_space_query(frm, { status: "Ready" }); },
        refresh(frm) {
            if (frm.is_new()) {
                frm.dashboard.set_headline(__("Choose a property, available room/unit and dates. EstateFlow will prevent overlaps automatically."));
            }
            if (frm.doc.docstatus === 0 && !frm.is_new()) {
                frm.add_custom_button(__("Confirm Reservation"), () => run_doc_method(frm, "confirm_reservation", {}, __("Confirming reservation…"))).addClass("btn-primary");
            }
            if (frm.doc.docstatus === 1 && ["Confirmed", "Tentative"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Check In"), () => run_doc_method(frm, "check_in", {}, __("Checking in…"))).addClass("btn-primary");
            }
            if (frm.doc.docstatus === 1 && frm.doc.status === "Checked In") {
                frm.add_custom_button(__("Check Out"), () => run_doc_method(frm, "check_out", {}, __("Checking out…"))).addClass("btn-primary");
            }
            if (frm.doc.docstatus === 1 && !frm.doc.sales_invoice) {
                frm.add_custom_button(__("Create Invoice"), async () => open_doc("Sales Invoice", await run_doc_method(frm, "create_sales_invoice")), __("Billing"));
            }
            if (frm.doc.sales_invoice) frm.add_custom_button(__("Open Invoice"), () => open_doc("Sales Invoice", frm.doc.sales_invoice), __("Billing"));
        },
    });

    frappe.ui.form.on("Occupancy Agreement", {
        setup(frm) { property_space_query(frm, { rentable: 1 }); },
        property(frm) { property_space_query(frm, { rentable: 1 }); },
        refresh(frm) {
            if (frm.is_new()) frm.dashboard.set_headline(__("Add the tenant, unit, term and recurring charges. Submitting activates occupancy and scheduled billing."));
            if (frm.doc.docstatus === 1 && ["Active", "Notice Given"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Create Current Invoice"), async () => open_doc("Sales Invoice", await run_doc_method(frm, "create_current_invoice")), __("Billing"));
                frm.add_custom_button(__("Record Deposit"), () => frappe.new_doc("Security Deposit Transaction", {
                    agreement: frm.doc.name, transaction_type: "Receipt", amount: frm.doc.security_deposit_amount,
                }), __("Deposit"));
                frm.add_custom_button(__("Deposit History"), () => frappe.set_route("List", "Security Deposit Transaction", { agreement: frm.doc.name }), __("Deposit"));
            }
            frm.add_custom_button(__("Rent Roll"), () => frappe.set_route("query-report", "Rent Roll", { property: frm.doc.property }));
        },
    });

    frappe.ui.form.on("Property Offer", {
        setup(frm) { property_space_query(frm); },
        property(frm) { property_space_query(frm); },
        refresh(frm) {
            if (frm.doc.docstatus === 1 && ["Submitted", "Under Review", "Countered"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Accept Offer"), () => run_doc_method(frm, "accept_offer")).addClass("btn-primary");
            }
            if (frm.doc.docstatus === 1 && frm.doc.status === "Accepted") {
                frm.add_custom_button(__("Create Reservation / Hold"), async () => open_doc("Property Reservation", await run_doc_method(frm, "create_reservation"))).addClass("btn-primary");
            }
        },
    });

    frappe.ui.form.on("Property Sale Contract", {
        setup(frm) { property_space_query(frm, { sellable: 1 }); },
        property(frm) { property_space_query(frm, { sellable: 1 }); },
        refresh(frm) {
            if (frm.is_new()) frm.dashboard.set_headline(__("The installment schedule must equal the contract value. Due installments flow directly to Sales Invoice."));
            if (frm.doc.docstatus === 1 && frm.doc.status === "Active") {
                frm.add_custom_button(__("Create Due Invoices"), () => run_doc_method(frm, "create_due_invoices"), __("Billing"));
                frm.add_custom_button(__("Mark Completed"), () => run_doc_method(frm, "mark_completed"));
            }
        },
    });

    frappe.ui.form.on("Maintenance Request", {
        setup(frm) { property_space_query(frm); },
        property(frm) { property_space_query(frm); },
        refresh(frm) {
            if (!frm.is_new() && !frm.doc.work_order && !["Closed", "Cancelled"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Create Work Order"), async () => open_doc("Property Work Order", await run_doc_method(frm, "create_work_order"))).addClass("btn-primary");
            }
            if (frm.doc.work_order) frm.add_custom_button(__("Open Work Order"), () => open_doc("Property Work Order", frm.doc.work_order));
        },
    });

    frappe.ui.form.on("Property Work Order", {
        setup(frm) { property_space_query(frm); },
        property(frm) { property_space_query(frm); },
        refresh(frm) {
            if (frm.doc.docstatus === 1 && ["Approved", "Scheduled"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Start Work"), () => run_doc_method(frm, "start_work")).addClass("btn-primary");
            }
            if (frm.doc.docstatus === 1 && ["In Progress", "Waiting for Material"].includes(frm.doc.status)) {
                frm.add_custom_button(__("Complete Work"), () => {
                    frappe.prompt({ fieldname: "notes", label: __("Completion Notes"), fieldtype: "Small Text", reqd: 1 },
                        (values) => run_doc_method(frm, "complete_work", { completion_notes: values.notes }), __("Complete Work"));
                }).addClass("btn-primary");
            }
            if (frm.doc.materials?.length) {
                frm.add_custom_button(__("Material Request"), async () => open_doc("Material Request", await run_doc_method(frm, "create_material_request")), __("Procurement"));
            }
        },
    });

    frappe.ui.form.on("Property Inspection", {
        setup(frm) { property_space_query(frm); },
        property(frm) { property_space_query(frm); },
        refresh(frm) {
            if (frm.doc.docstatus === 1 && frm.doc.items?.some((row) => row.maintenance_required)) {
                frm.add_custom_button(__("Create Maintenance Requests"), () => run_doc_method(frm, "create_maintenance_requests"));
            }
        },
    });

    frappe.ui.form.on("Utility Meter", {
        setup(frm) { property_space_query(frm); },
        property(frm) { property_space_query(frm); },
        refresh(frm) {
            if (!frm.is_new()) frm.add_custom_button(__("New Reading"), () => frappe.new_doc("Utility Reading", { meter: frm.doc.name }));
        },
    });

    frappe.ui.form.on("Utility Reading", {
        refresh(frm) {
            if (frm.doc.docstatus === 1 && !frm.doc.sales_invoice && frm.doc.customer) {
                frm.add_custom_button(__("Create Utility Invoice"), async () => open_doc("Sales Invoice", await run_doc_method(frm, "create_sales_invoice"))).addClass("btn-primary");
            }
            if (frm.doc.sales_invoice) frm.add_custom_button(__("Open Invoice"), () => open_doc("Sales Invoice", frm.doc.sales_invoice));
        },
    });

    frappe.ui.form.on("Security Deposit Transaction", {
        setup(frm) {
            ["liability_account", "bank_account", "adjustment_account"].forEach((fieldname) => {
                frm.set_query(fieldname, () => ({ filters: { company: frm.doc.company, is_group: 0 } }));
            });
            frm.set_query("sales_invoice", () => ({ filters: {
                customer: frm.doc.customer, company: frm.doc.company, docstatus: 1,
                outstanding_amount: [">", 0], estateflow_agreement: frm.doc.agreement,
            } }));
        },
        refresh(frm) {
            if (frm.doc.journal_entry) frm.add_custom_button(__("Open Journal Entry"), () => open_doc("Journal Entry", frm.doc.journal_entry));
            if (frm.is_new()) frm.dashboard.set_headline(__("Submission posts an auditable Journal Entry. Refunds and deductions cannot exceed the available deposit balance."));
        },
    });

    frappe.ui.form.on("Property Allocation", {
        setup(frm) { property_space_query(frm, { allocatable: 1 }); },
        property(frm) { property_space_query(frm, { allocatable: 1 }); },
        refresh(frm) {
            if (frm.doc.docstatus !== 1) return;
            if (frm.doc.allocation_type === "Purchase" && !frm.doc.sale_contract) {
                frm.add_custom_button(__("Create Sale Contract"), async () => open_doc("Property Sale Contract", await run_doc_method(frm, "create_sale_contract"))).addClass("btn-primary");
            } else if (frm.doc.allocation_type !== "Purchase" && !frm.doc.occupancy_agreement) {
                frm.add_custom_button(__("Create Occupancy Agreement"), async () => open_doc("Occupancy Agreement", await run_doc_method(frm, "create_occupancy_agreement"))).addClass("btn-primary");
            }
        },
    });
})();
