frappe.query_reports["Rent Roll"] = {
    filters: [
        { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") },
        { fieldname: "property", label: __("Property"), fieldtype: "Link", options: "Real Estate Property" },
        { fieldname: "status", label: __("Status"), fieldtype: "Select", options: "\nActive\nNotice Given\nExpired\nTerminated", default: "Active" },
        { fieldname: "as_on_date", label: __("As On"), fieldtype: "Date", default: frappe.datetime.get_today() },
    ],
};
