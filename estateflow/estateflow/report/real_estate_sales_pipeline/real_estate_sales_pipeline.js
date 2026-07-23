frappe.query_reports["Real Estate Sales Pipeline"] = { filters: [
 {fieldname:"assigned_to",label:__("Agent / Officer"),fieldtype:"Link",options:"User"},
 {fieldname:"enquiry_type",label:__("Interested In"),fieldtype:"Select",options:"\nLong-term Rent\nPurchase\nShort Stay\nHousing Application\nProperty Management\nOther"},
 {fieldname:"status",label:__("Status"),fieldtype:"Select",options:"\nNew\nContacted\nQualified\nViewing Scheduled\nOffer Made\nConverted\nLost"},
]};
