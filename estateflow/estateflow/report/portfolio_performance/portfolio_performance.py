import frappe
from frappe import _


def execute(filters=None):
    f=frappe._dict(filters or {}); values={'company':f.company,'from_date':f.from_date,'to_date':f.to_date}; extra=''
    if f.portfolio: extra=' and p.portfolio=%(portfolio)s'; values['portfolio']=f.portfolio
    columns=[
      {"label":_("Portfolio"),"fieldname":"portfolio","fieldtype":"Link","options":"Property Portfolio","width":180},
      {"label":_("Property"),"fieldname":"property","fieldtype":"Link","options":"Real Estate Property","width":180},
      {"label":_("Currency"),"fieldname":"currency","fieldtype":"Link","options":"Currency","width":75},
      {"label":_("Spaces"),"fieldname":"spaces","fieldtype":"Int","width":75},{"label":_("Occupied"),"fieldname":"occupied","fieldtype":"Int","width":80},
      {"label":_("Available"),"fieldname":"available","fieldtype":"Int","width":80},{"label":_("Occupancy %"),"fieldname":"occupancy","fieldtype":"Percent","width":95},
      {"label":_("Billed"),"fieldname":"billed","fieldtype":"Currency","options":"currency","width":120},
      {"label":_("Collected"),"fieldname":"collected","fieldtype":"Currency","options":"currency","width":120},
      {"label":_("Outstanding"),"fieldname":"outstanding","fieldtype":"Currency","options":"currency","width":120},
      {"label":_("Purchase Expense"),"fieldname":"expense","fieldtype":"Currency","options":"currency","width":125},
      {"label":_("Operating Margin"),"fieldname":"operating_margin","fieldtype":"Currency","options":"currency","width":130},
    ]
    data=frappe.db.sql(f"""
      select p.portfolio,p.name property,p.currency,
       (select count(*) from `tabProperty Space` s where s.property=p.name) spaces,
       (select count(*) from `tabProperty Space` s where s.property=p.name and s.occupancy_status in ('Occupied','Owner Occupied')) occupied,
       (select count(*) from `tabProperty Space` s where s.property=p.name and s.occupancy_status='Available') available,
       coalesce((select sum(si.grand_total) from `tabSales Invoice` si where si.docstatus=1 and si.estateflow_property=p.name and si.posting_date between %(from_date)s and %(to_date)s),0) billed,
       coalesce((select sum(si.grand_total-si.outstanding_amount) from `tabSales Invoice` si where si.docstatus=1 and si.estateflow_property=p.name and si.posting_date between %(from_date)s and %(to_date)s),0) collected,
       coalesce((select sum(si.outstanding_amount) from `tabSales Invoice` si where si.docstatus=1 and si.estateflow_property=p.name),0) outstanding,
       coalesce((select sum(pi.grand_total) from `tabPurchase Invoice` pi where pi.docstatus=1 and pi.estateflow_property=p.name and pi.posting_date between %(from_date)s and %(to_date)s),0) expense
      from `tabReal Estate Property` p where p.company=%(company)s {extra} order by p.portfolio,p.property_name
    """,values,as_dict=True)
    for row in data:
        base=max(0,(row.spaces or 0)); row.occupancy=(row.occupied/base*100) if base else 0; row.operating_margin=row.billed-row.expense
    return columns,data
