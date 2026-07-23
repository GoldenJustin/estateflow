frappe.ui.form.on("Property Portfolio", {
    refresh(frm) {
        frm.dashboard.set_headline(__("A portfolio is the management and reporting group above properties—for example one owner, housing program, hotel group, development, branch or investment fund."));
        if (!frm.is_new()) {
            frm.add_custom_button(__("Add Property"), () => frappe.new_doc("Real Estate Property", { portfolio: frm.doc.name, company: frm.doc.company }));
            frm.add_custom_button(__("Portfolio Performance"), () => frappe.set_route("query-report", "Portfolio Performance", { company: frm.doc.company, portfolio: frm.doc.name }));
        }
    },
});
