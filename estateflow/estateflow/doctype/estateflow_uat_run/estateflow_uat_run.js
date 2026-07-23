frappe.ui.form.on("EstateFlow UAT Run", {
    refresh(frm) {
        frm.dashboard.set_headline(__("Use one UAT Run per client and business case. Record actual result and evidence for every test, then submit for a controlled pass/fail result."));
        if (frm.doc.docstatus === 0 && !frm.is_new()) {
            frm.add_custom_button(__("Reload Test Template"), async () => {
                frappe.confirm(__("This replaces all current test rows. Continue?"), async () => {
                    const response = await frm.call("reload_template");
                    await frm.reload_doc();
                    frappe.show_alert(__("Loaded {0} tests", [response.message]));
                });
            });
        }
        frm.add_custom_button(__("UAT Summary"), () => frappe.set_route("query-report", "EstateFlow UAT Summary", { uat_run: frm.doc.name }));
    },
});

frappe.ui.form.on("EstateFlow UAT Result", {
    status(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        if (["Pass", "Fail", "Blocked"].includes(row.status)) {
            frappe.model.set_value(cdt, cdn, "tested_by", frappe.session.user);
            frappe.model.set_value(cdt, cdn, "tested_on", frappe.datetime.now_datetime());
        }
    },
});
