frappe.query_reports["Hotel Operations"] = { filters: [
 {fieldname:"property",label:__("Hotel / Lodge"),fieldtype:"Link",options:"Real Estate Property"},
 {fieldname:"from_date",label:__("Arrival From"),fieldtype:"Date",default:frappe.datetime.get_today()},
 {fieldname:"to_date",label:__("Arrival To"),fieldtype:"Date",default:frappe.datetime.add_days(frappe.datetime.get_today(),30)},
 {fieldname:"status",label:__("Status"),fieldtype:"Select",options:"\nConfirmed\nChecked In\nChecked Out\nCancelled\nNo Show"},
]};
