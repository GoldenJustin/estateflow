import frappe
from frappe import _


def execute(filters=None):
    f=frappe._dict(filters or {}); values={}; cond=["1=1"]
    for key in ("company","property","customer","status"):
        if f.get(key): cond.append(f"e.{key} = %({key})s"); values[key]=f.get(key)
    if f.from_date: cond.append("e.posting_date >= %(from_date)s"); values['from_date']=f.from_date
    if f.to_date: cond.append("e.posting_date <= %(to_date)s"); values['to_date']=f.to_date
    columns=[
      {"label":_("Invoice"),"fieldname":"sales_invoice","fieldtype":"Link","options":"Sales Invoice","width":145},
      {"label":_("Source"),"fieldname":"billing_source","width":145},{"label":_("Contract Type"),"fieldname":"reference_doctype","width":145},
      {"label":_("Contract"),"fieldname":"reference_name","fieldtype":"Dynamic Link","options":"reference_doctype","width":150},
      {"label":_("Property"),"fieldname":"property","fieldtype":"Link","options":"Real Estate Property","width":160},
      {"label":_("Space"),"fieldname":"space","fieldtype":"Link","options":"Property Space","width":130},
      {"label":_("Customer"),"fieldname":"customer","fieldtype":"Link","options":"Customer","width":170},
      {"label":_("Posting"),"fieldname":"posting_date","fieldtype":"Date","width":90},{"label":_("Due"),"fieldname":"due_date","fieldtype":"Date","width":90},
      {"label":_("Currency"),"fieldname":"currency","fieldtype":"Link","options":"Currency","width":75},
      {"label":_("Billed"),"fieldname":"billed_amount","fieldtype":"Currency","options":"currency","width":110},
      {"label":_("Paid"),"fieldname":"paid_amount","fieldtype":"Currency","options":"currency","width":110},
      {"label":_("Outstanding"),"fieldname":"outstanding_amount","fieldtype":"Currency","options":"currency","width":115},
      {"label":_("Status"),"fieldname":"status","width":90},
    ]
    data=frappe.db.sql(f"select e.* from `tabContract Billing Event` e where {' and '.join(cond)} order by e.posting_date desc,e.modified desc",values,as_dict=True)
    return columns,data
