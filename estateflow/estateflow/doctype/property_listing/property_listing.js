frappe.ui.form.on("Property Listing", {
    setup(frm) {
        frm.set_query("space", () => ({ filters: { property: frm.doc.property } }));
    },
    refresh(frm) {
        frm.dashboard.set_headline(__("Active listings with Publish enabled appear at /properties. The Featured Image is shown on the public card and detail page."));
        if (!frm.is_new() && frm.doc.status !== "Active") {
            frm.add_custom_button(__("Activate and Publish"), async () => {
                const response = await frm.call("activate_listing");
                await frm.reload_doc();
                if (response.message) window.open(`/${response.message}`, "_blank");
            }).addClass("btn-primary");
        }
        if (frm.doc.status === "Active" && frm.doc.publish_on_website && frm.doc.website_route) {
            frm.add_custom_button(__("View Public Listing"), () => window.open(`/${frm.doc.website_route}`, "_blank")).addClass("btn-primary");
            frm.add_custom_button(__("All Public Listings"), () => window.open("/properties", "_blank"));
        }
    },
});
