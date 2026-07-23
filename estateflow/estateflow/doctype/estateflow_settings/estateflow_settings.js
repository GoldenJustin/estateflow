frappe.ui.form.on("EstateFlow Settings", {
    refresh(frm) {
        frm.dashboard.set_headline(__("Billing scheduler runs daily. Contracts can invoice on activation, period start, or configured lead days. Email notifications remain off until enabled and an outgoing Email Account is configured."));
        frm.add_custom_button(__("Run Billing Now"), async () => {
            await frappe.call({ method: "estateflow.api.billing.run_daily_billing", freeze: true, freeze_message: __("Running EstateFlow billing…") });
            frappe.show_alert({ message: __("Billing run completed; review Contract Billing Tracker and Error Log."), indicator: "green" });
        }, __("Automation"));
        frm.add_custom_button(__("Run Contract Lifecycle Now"), async () => {
            await frappe.call({ method: "estateflow.api.operations.run_daily_operations", freeze: true });
            frappe.show_alert({ message: __("Contract activation/expiry run completed."), indicator: "green" });
        }, __("Automation"));
        frm.add_custom_button(__("Run Email Reminders Now"), async () => {
            await frappe.call({ method: "estateflow.api.notifications.run_daily_notifications", freeze: true });
            frappe.set_route("List", "EstateFlow Notification Log");
        }, __("Automation"));
        frm.add_custom_button(__("Rebuild Billing Tracker"), async () => {
            const response = await frappe.call({ method: "estateflow.api.billing_tracking.rebuild_billing_ledger", args: { company: frm.doc.company }, freeze: true });
            frappe.msgprint(__("Processed {0} property invoice(s).", [response.message.processed]));
        }, __("Automation"));
        frm.add_custom_button(__("Notification Log"), () => frappe.set_route("List", "EstateFlow Notification Log"), __("Review"));
        frm.add_custom_button(__("Contract Billing Tracker"), () => frappe.set_route("query-report", "Contract Billing Tracker"), __("Review"));
        frm.add_custom_button(__("Client Test Center"), () => frappe.set_route("estateflow-test-center"), __("Review"));
    },
});
