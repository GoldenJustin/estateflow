import frappe
from frappe import _


def execute(filters=None):
 f=frappe._dict(filters or {});v={};c=['1=1']
 if f.uat_run:c.append("u.name=%(run)s");v['run']=f.uat_run
 if f.business_case:c.append("u.business_case=%(business_case)s");v['business_case']=f.business_case
 if f.status:c.append("r.status=%(status)s");v['status']=f.status
 cols=[{"label":_("UAT Run"),"fieldname":"uat_run","fieldtype":"Link","options":"EstateFlow UAT Run","width":135},{"label":_("Business Case"),"fieldname":"business_case","width":165},{"label":_("Test ID"),"fieldname":"test_id","width":85},{"label":_("Module"),"fieldname":"module","width":110},{"label":_("Scenario"),"fieldname":"scenario","width":240},{"label":_("Expected Result"),"fieldname":"expected_result","width":300},{"label":_("Status"),"fieldname":"status","width":90},{"label":_("Severity"),"fieldname":"severity","width":80},{"label":_("Tested By"),"fieldname":"tested_by","fieldtype":"Link","options":"User","width":140},{"label":_("Issue"),"fieldname":"issue_reference","width":120}]
 data=frappe.db.sql(f"""select u.name uat_run,u.business_case,r.test_id,r.module,r.scenario,r.expected_result,r.status,r.severity,r.tested_by,r.issue_reference from `tabEstateFlow UAT Run` u inner join `tabEstateFlow UAT Result` r on r.parent=u.name and r.parenttype='EstateFlow UAT Run' where {' and '.join(c)} order by u.modified desc,r.idx""",v,as_dict=True)
 return cols,data
