frappe.query_reports["Contract Billing Tracker"] = { filters: [
 {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company",default:frappe.defaults.get_user_default("Company")},
 {fieldname:"property",label:__("Property"),fieldtype:"Link",options:"Real Estate Property"},
 {fieldname:"customer",label:__("Customer"),fieldtype:"Link",options:"Customer"},
 {fieldname:"status",label:__("Status"),fieldtype:"Select",options:"\nDraft\nUnpaid\nPartly Paid\nPaid\nOverdue\nCancelled"},
 {fieldname:"from_date",label:__("From"),fieldtype:"Date",default:frappe.datetime.add_months(frappe.datetime.get_today(),-1)},
 {fieldname:"to_date",label:__("To"),fieldtype:"Date",default:frappe.datetime.get_today()},
]};
