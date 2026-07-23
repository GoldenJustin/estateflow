import frappe
from frappe import _


def execute(filters=None):
 f=frappe._dict(filters or {}); v={'from':f.from_date,'to':f.to_date}; c=["r.reservation_type='Hotel / Lodge Stay'","r.arrival_date between %(from)s and %(to)s","r.docstatus<2"]
 if f.property:c.append("r.property=%(property)s");v['property']=f.property
 if f.status:c.append("r.status=%(status)s");v['status']=f.status
 cols=[{"label":_("Reservation"),"fieldname":"name","fieldtype":"Link","options":"Property Reservation","width":140},{"label":_("Property"),"fieldname":"property","fieldtype":"Link","options":"Real Estate Property","width":160},{"label":_("Room"),"fieldname":"space","fieldtype":"Link","options":"Property Space","width":130},{"label":_("Guest"),"fieldname":"guest","width":160},{"label":_("Arrival"),"fieldname":"arrival_date","fieldtype":"Date","width":90},{"label":_("Departure"),"fieldname":"departure_date","fieldtype":"Date","width":90},{"label":_("Nights"),"fieldname":"number_of_nights","fieldtype":"Int","width":65},{"label":_("Status"),"fieldname":"status","width":90},{"label":_("Housekeeping"),"fieldname":"housekeeping_status","width":100},{"label":_("Currency"),"fieldname":"currency","width":70},{"label":_("Total"),"fieldname":"grand_total","fieldtype":"Currency","options":"currency","width":110},{"label":_("Invoice"),"fieldname":"sales_invoice","fieldtype":"Link","options":"Sales Invoice","width":135},{"label":_("Outstanding"),"fieldname":"outstanding","fieldtype":"Currency","options":"currency","width":110}]
 data=frappe.db.sql(f"""select r.name,r.property,r.space,coalesce(r.guest_name,r.customer) guest,r.arrival_date,r.departure_date,r.number_of_nights,r.status,s.housekeeping_status,r.currency,r.grand_total,r.sales_invoice,coalesce(si.outstanding_amount,0) outstanding from `tabProperty Reservation` r left join `tabProperty Space` s on s.name=r.space left join `tabSales Invoice` si on si.name=r.sales_invoice where {' and '.join(c)} order by r.arrival_date,r.property,r.space""",v,as_dict=True)
 return cols,data
