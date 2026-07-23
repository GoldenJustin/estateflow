frappe.pages["estateflow-test-center"].on_page_load = function (wrapper) {
    frappe.estateflow_test_center = new EstateFlowTestCenter(wrapper);
};

class EstateFlowTestCenter {
    constructor(wrapper) {
        this.page = frappe.ui.make_app_page({ parent: wrapper, title: __("EstateFlow Test Center"), single_column: true });
        this.page.main.addClass("ef-test-center");
        this.page.add_inner_button(__("Download Excel UAT Workbook"), () => window.open("/assets/estateflow/files/EstateFlow_UAT_Testing_Template.xlsx", "_blank"));
        this.page.add_inner_button(__("Operating Guide"), () => frappe.set_route("estateflow-guide"));
        this.businessCases = ["Individual Landlord","Hotel / Lodge","Property Management","Agency / Brokerage","National / Social Housing","Developer Sales","Commercial / Retail / Warehouse","HOA / Community","Investment Portfolio / REIT","Facilities and Maintenance","Complete Suite"];
        this.make();
    }
    make() {
        this.page.main.html(`<section class="ef-test-hero"><small>CLIENT DEMONSTRATION & USER ACCEPTANCE</small><h2>${__("Prove the complete business outcome")}</h2><p>${__("Select a business case, preview every required test, create a controlled UAT Run, attach evidence and obtain client sign-off.")}</p></section><section class="ef-test-controls"><div class="business-control"></div><div class="company-control"></div><button class="btn btn-primary create-run">${__("Create UAT Run")}</button></section><section class="ef-guide-card"><span class="ef-eyebrow">${__("TEST TEMPLATE")}</span><h3 class="test-title"></h3><p class="test-count"></p><div class="ef-test-preview"></div></section><section class="ef-guide-card"><span class="ef-eyebrow">${__("REPORT RECONCILIATION")}</span><h3>${__("Every demonstration must finish with these reports")}</h3><div class="ef-report-catalog">${this.reports().map(r=>`<button data-report="${r}"><b>${__(r)}</b><small>${__("Open report")}</small></button>`).join("")}</div></section>`);
        this.business = frappe.ui.form.make_control({ parent:this.page.main.find('.business-control'), df:{fieldtype:'Select',label:__('Business Case'),options:this.businessCases.join('\n'),reqd:1}, render_input:true });
        this.company = frappe.ui.form.make_control({ parent:this.page.main.find('.company-control'), df:{fieldtype:'Link',label:__('Company'),options:'Company',reqd:1,default:frappe.defaults.get_user_default('Company')}, render_input:true });
        this.business.set_value(this.businessCases[0]);
        this.business.df.onchange=()=>this.load();
        this.page.main.on('click','.create-run',()=>this.createRun());
        this.page.main.on('click','[data-report]',e=>frappe.set_route('query-report',$(e.currentTarget).data('report')));
        this.load();
    }
    reports(){return ["Contract Billing Tracker","Portfolio Performance","Hotel Operations","Maintenance SLA","Real Estate Sales Pipeline","Housing Allocation Register","EstateFlow UAT Summary","Rent Roll","Lease Expiry"]}
    async load(){const type=this.business.get_value();const r=await frappe.call('estateflow.api.uat.preview_test_template',{business_case:type});const rows=r.message||[];this.page.main.find('.test-title').text(type);this.page.main.find('.test-count').text(__("{0} controlled test cases",[rows.length]));this.page.main.find('.ef-test-preview').html(rows.map(x=>`<article class="ef-test-row"><b>${frappe.utils.escape_html(x.test_id)}</b><b>${frappe.utils.escape_html(x.module)}</b><p><strong>${frappe.utils.escape_html(x.scenario)}</strong><br>${frappe.utils.escape_html(x.expected_result)}</p><b>${frappe.utils.escape_html(x.severity)}</b></article>`).join(''))}
    createRun(){const type=this.business.get_value(),company=this.company.get_value();if(!type||!company){frappe.msgprint(__("Select business case and company."));return}frappe.new_doc('EstateFlow UAT Run',{business_case:type,company,title:`${type} UAT - ${company}`,test_date:frappe.datetime.get_today()})}
}
