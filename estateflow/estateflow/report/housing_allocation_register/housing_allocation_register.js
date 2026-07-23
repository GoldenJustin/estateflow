frappe.query_reports["Housing Allocation Register"] = { filters: [
 {fieldname:"property",label:__("Scheme / Property"),fieldtype:"Link",options:"Real Estate Property"},
 {fieldname:"allocation_type",label:__("Allocation Type"),fieldtype:"Select",options:"\nRental\nPurchase\nStaff Housing\nStudent Housing\nEmergency / Temporary"},
 {fieldname:"status",label:__("Status"),fieldtype:"Select",options:"\nProposed\nApproved\nAccepted\nDeclined\nConverted\nCancelled"},
]};
