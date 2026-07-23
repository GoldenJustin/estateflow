import frappe
from frappe import _


def execute(filters=None):
 f=frappe._dict(filters or {});v={};c=["m.status!='Cancelled'"]
 for k in ('property','status','priority'):
  if f.get(k):c.append(f"m.{k}=%({k})s");v[k]=f.get(k)
 if f.only_overdue:c.append("m.sla_due_on<now() and m.status not in ('Resolved','Closed')")
 cols=[{"label":_("Request"),"fieldname":"name","fieldtype":"Link","options":"Maintenance Request","width":140},{"label":_("Subject"),"fieldname":"subject","width":190},{"label":_("Property"),"fieldname":"property","fieldtype":"Link","options":"Real Estate Property","width":150},{"label":_("Space"),"fieldname":"space","fieldtype":"Link","options":"Property Space","width":120},{"label":_("Priority"),"fieldname":"priority","width":80},{"label":_("Status"),"fieldname":"status","width":90},{"label":_("Reported"),"fieldname":"reported_on","fieldtype":"Datetime","width":135},{"label":_("SLA Due"),"fieldname":"sla_due_on","fieldtype":"Datetime","width":135},{"label":_("SLA"),"fieldname":"sla_status","width":85},{"label":_("Assigned"),"fieldname":"assigned_to","fieldtype":"Link","options":"User","width":140},{"label":_("Work Order"),"fieldname":"work_order","fieldtype":"Link","options":"Property Work Order","width":135}]
 data=frappe.db.sql(f"""select m.*,case when m.status in ('Resolved','Closed') then 'Completed' when m.sla_due_on<now() then 'Overdue' else 'Within SLA' end sla_status from `tabMaintenance Request` m where {' and '.join(c)} order by field(m.priority,'Emergency','High','Medium','Low'),m.sla_due_on""",v,as_dict=True)
 return cols,data
