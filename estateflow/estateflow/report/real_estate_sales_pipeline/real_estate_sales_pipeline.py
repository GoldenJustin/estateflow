import frappe
from frappe import _


def execute(filters=None):
 f=frappe._dict(filters or {});v={};c=['1=1']
 for k in ('assigned_to','enquiry_type','status'):
  if f.get(k):c.append(f"e.{k}=%({k})s");v[k]=f.get(k)
 cols=[{"label":_("Enquiry"),"fieldname":"name","fieldtype":"Link","options":"Property Enquiry","width":140},{"label":_("Contact"),"fieldname":"contact_name","width":160},{"label":_("Interested In"),"fieldname":"enquiry_type","width":130},{"label":_("Property"),"fieldname":"property","fieldtype":"Link","options":"Real Estate Property","width":150},{"label":_("Space"),"fieldname":"space","fieldtype":"Link","options":"Property Space","width":120},{"label":_("Agent"),"fieldname":"assigned_to","fieldtype":"Link","options":"User","width":140},{"label":_("Status"),"fieldname":"status","width":100},{"label":_("Priority"),"fieldname":"priority","width":75},{"label":_("Viewings"),"fieldname":"viewings","fieldtype":"Int","width":70},{"label":_("Offers"),"fieldname":"offers","fieldtype":"Int","width":65},{"label":_("Best Offer"),"fieldname":"best_offer","fieldtype":"Currency","options":"currency","width":110},{"label":_("Currency"),"fieldname":"currency","width":70}]
 data=frappe.db.sql(f"""select e.*,(select count(*) from `tabViewing Appointment` v where v.enquiry=e.name) viewings,(select count(*) from `tabProperty Offer` o where o.enquiry=e.name and o.docstatus<2) offers,(select max(o.offered_amount) from `tabProperty Offer` o where o.enquiry=e.name and o.docstatus<2) best_offer from `tabProperty Enquiry` e where {' and '.join(c)} order by e.modified desc""",v,as_dict=True)
 return cols,data
