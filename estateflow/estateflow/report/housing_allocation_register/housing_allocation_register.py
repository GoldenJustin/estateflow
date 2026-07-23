import frappe
from frappe import _


def execute(filters=None):
 f=frappe._dict(filters or {});v={};c=['a.docstatus<2']
 for k in ('property','allocation_type','status'):
  if f.get(k):c.append(f"a.{k}=%({k})s");v[k]=f.get(k)
 cols=[{"label":_("Allocation"),"fieldname":"name","fieldtype":"Link","options":"Property Allocation","width":140},{"label":_("Application"),"fieldname":"housing_application","fieldtype":"Link","options":"Housing Application","width":140},{"label":_("Applicant"),"fieldname":"customer","fieldtype":"Link","options":"Customer","width":170},{"label":_("Property"),"fieldname":"property","fieldtype":"Link","options":"Real Estate Property","width":160},{"label":_("Space"),"fieldname":"space","fieldtype":"Link","options":"Property Space","width":130},{"label":_("Type"),"fieldname":"allocation_type","width":120},{"label":_("Date"),"fieldname":"allocation_date","fieldtype":"Date","width":90},{"label":_("Status"),"fieldname":"status","width":90},{"label":_("Currency"),"fieldname":"currency","width":70},{"label":_("Amount"),"fieldname":"amount","fieldtype":"Currency","options":"currency","width":110},{"label":_("Agreement"),"fieldname":"occupancy_agreement","fieldtype":"Link","options":"Occupancy Agreement","width":140},{"label":_("Sale"),"fieldname":"sale_contract","fieldtype":"Link","options":"Property Sale Contract","width":140}]
 data=frappe.db.sql(f"select a.* from `tabProperty Allocation` a where {' and '.join(c)} order by a.allocation_date desc",v,as_dict=True)
 return cols,data
