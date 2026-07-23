frappe.query_reports["EstateFlow UAT Summary"] = { filters: [
 {fieldname:"uat_run",label:__("UAT Run"),fieldtype:"Link",options:"EstateFlow UAT Run"},
 {fieldname:"business_case",label:__("Business Case"),fieldtype:"Select",options:"\nIndividual Landlord\nHotel / Lodge\nProperty Management\nAgency / Brokerage\nNational / Social Housing\nDeveloper Sales\nCommercial / Retail / Warehouse\nHOA / Community\nInvestment Portfolio / REIT\nFacilities and Maintenance\nComplete Suite"},
 {fieldname:"status",label:__("Test Status"),fieldtype:"Select",options:"\nNot Tested\nPass\nFail\nBlocked\nNot Applicable"},
]};
