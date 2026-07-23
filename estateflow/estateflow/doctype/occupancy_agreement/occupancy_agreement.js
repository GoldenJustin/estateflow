frappe.ui.form.on("Occupancy Agreement", {
    setup(frm) {
        frm.set_query("space", () => ({ filters: { property: frm.doc.property, rentable: 1 } }));
    },
    refresh(frm) {
        frm.dashboard.set_headline(__("Submitting reserves or activates the unit. Billing can run on activation, period start, or configured days before the period. Every linked invoice is tracked in Contract Billing Event."));
        if (frm.doc.docstatus !== 1) return;
        if (frm.doc.status === "Pending Activation") {
            frm.add_custom_button(__("Activate Now"), async () => {
                await frm.call("activate_contract");
                await frm.reload_doc();
            }).addClass("btn-primary");
        }
        if (["Pending Activation", "Active", "Notice Given"].includes(frm.doc.status)) {
            frm.add_custom_button(__("Generate Due Invoices"), async () => {
                const response = await frm.call("create_due_invoices");
                frappe.msgprint(__("Generated or found {0} invoice(s).", [(response.message || []).length]));
                await frm.reload_doc();
            }, __("Billing"));
            frm.add_custom_button(__("Billing Tracker"), () => frappe.set_route("List", "Contract Billing Event", { reference_doctype: "Occupancy Agreement", reference_name: frm.doc.name }), __("Billing"));
            frm.add_custom_button(__("Sync Existing Invoice Links"), async () => {
                const response = await frappe.call("estateflow.api.billing_tracking.rebuild_billing_ledger", { company: frm.doc.company });
                frappe.show_alert(__("Processed {0} property invoice(s)", [response.message.processed]));
            }, __("Billing"));
            frm.add_custom_button(__("Record Deposit"), () => frappe.new_doc("Security Deposit Transaction", { agreement: frm.doc.name, transaction_type: "Receipt", amount: frm.doc.security_deposit_amount }), __("Deposit"));
            frm.add_custom_button(__("Expire Now"), async () => {
                await frm.call("expire_contract");
                await frm.reload_doc();
            }, __("Status"));
        }
        frm.add_custom_button(__("Rent Roll"), () => frappe.set_route("query-report", "Rent Roll", { property: frm.doc.property }));
    },
});
