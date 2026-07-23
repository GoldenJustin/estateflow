frappe.query_reports["Portfolio Performance"] = { filters: [
 {fieldname:"company",label:__("Company"),fieldtype:"Link",options:"Company",default:frappe.defaults.get_user_default("Company"),reqd:1},
 {fieldname:"portfolio",label:__("Portfolio"),fieldtype:"Link",options:"Property Portfolio"},
 {fieldname:"from_date",label:__("From"),fieldtype:"Date",default:frappe.datetime.year_start()},
 {fieldname:"to_date",label:__("To"),fieldtype:"Date",default:frappe.datetime.get_today()},
]};
