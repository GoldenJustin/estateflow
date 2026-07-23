frappe.query_reports["Maintenance SLA"] = { filters: [
 {fieldname:"property",label:__("Property"),fieldtype:"Link",options:"Real Estate Property"},
 {fieldname:"status",label:__("Status"),fieldtype:"Select",options:"\nOpen\nAcknowledged\nAssigned\nIn Progress\nOn Hold\nResolved\nClosed"},
 {fieldname:"priority",label:__("Priority"),fieldtype:"Select",options:"\nLow\nMedium\nHigh\nEmergency"},
 {fieldname:"only_overdue",label:__("Only Beyond SLA"),fieldtype:"Check"},
]};
