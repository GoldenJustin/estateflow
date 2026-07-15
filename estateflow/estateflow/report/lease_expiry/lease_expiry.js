frappe.query_reports["Lease Expiry"] = {
    filters: [
        { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") },
        { fieldname: "property", label: __("Property"), fieldtype: "Link", options: "Real Estate Property" },
        { fieldname: "from_date", label: __("From"), fieldtype: "Date", default: frappe.datetime.get_today(), reqd: 1 },
        { fieldname: "to_date", label: __("To"), fieldtype: "Date", default: frappe.datetime.add_months(frappe.datetime.get_today(), 3), reqd: 1 },
    ],
};
