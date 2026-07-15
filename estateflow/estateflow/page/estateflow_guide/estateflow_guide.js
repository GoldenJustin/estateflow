function ensure_estateflow_guide_styles() {
    [
        ["estateflow-command-center-styles", "/assets/estateflow/css/estateflow.css?v=0.1.4"],
        ["estateflow-guide-styles", "/assets/estateflow/css/estateflow-guide.css?v=0.1.4"],
    ].forEach(([id, href]) => {
        if (document.getElementById(id)) return;
        const link = document.createElement("link");
        link.id = id;
        link.rel = "stylesheet";
        link.href = href;
        document.head.appendChild(link);
    });
}

frappe.pages["estateflow-guide"].on_page_load = function (wrapper) {
    ensure_estateflow_guide_styles();
    frappe.estateflow_guide = new EstateFlowGuide(wrapper);
};

frappe.pages["estateflow-guide"].on_page_show = function () {
    frappe.estateflow_guide?.refresh();
};

class EstateFlowGuide {
    constructor(wrapper) {
        this.page = frappe.ui.make_app_page({ parent: wrapper, title: __("EstateFlow Guide"), single_column: true });
        this.page.set_primary_action(__("Run Guided Setup"), () => this.show_setup(), "setting-gear");
        this.page.add_inner_button(__("Command Center"), () => frappe.set_route("estateflow-command-center"));
        this.page.add_menu_item(__("EstateFlow Settings"), () => frappe.set_route("Form", "EstateFlow Settings", "EstateFlow Settings"));
        this.page.main.addClass("estateflow-guide");
        this.active_section = "start";
        this.make_shell();
        this.bind();
        this.refresh();
    }

    make_shell() {
        this.page.main.html(`
            <section class="ef-guide-hero">
                <div><span class="ef-eyebrow">${__("ESTATEFLOW OPERATING MANUAL")}</span>
                <h2>${__("From first setup to daily operations")}</h2>
                <p>${__("Choose a business playbook and follow the exact records, decisions and accounting documents used at every step.")}</p></div>
                <div class="ef-guide-progress"><strong>0%</strong><span>${__("Setup progress")}</span></div>
            </section>
            <nav class="ef-guide-nav">
                ${this.nav_button("start", __("Start here"))}
                ${this.nav_button("playbooks", __("Business playbooks"))}
                ${this.nav_button("accounting", __("Accounting & buying"))}
                ${this.nav_button("roles", __("Roles & daily work"))}
                ${this.nav_button("help", __("Troubleshooting"))}
            </nav>
            <div class="ef-guide-loading">${__("Reading your EstateFlow configuration…")}</div>
            <main class="ef-guide-content"></main>
        `);
    }

    nav_button(key, label) {
        return `<button data-section="${key}" class="${key === this.active_section ? "active" : ""}">${label}</button>`;
    }

    bind() {
        this.page.main.on("click", ".ef-guide-nav button", (event) => {
            this.active_section = $(event.currentTarget).data("section");
            this.page.main.find(".ef-guide-nav button").removeClass("active");
            $(event.currentTarget).addClass("active");
            this.render_section();
        });
        this.page.main.on("click", "[data-route]", (event) => {
            const route = $(event.currentTarget).data("route");
            if (route) frappe.set_route(String(route).split("/"));
        });
        this.page.main.on("click", "[data-playbook]", (event) => {
            const key = $(event.currentTarget).data("playbook");
            this.page.main.find("[data-playbook]").removeClass("active");
            $(event.currentTarget).addClass("active");
            this.render_playbook(key);
        });
        this.page.main.on("click", ".ef-run-setup", () => this.show_setup());
    }

    async refresh() {
        this.page.main.find(".ef-guide-loading").show();
        const response = await frappe.call("estateflow.api.guide.get_guide_context");
        this.context = response.message || {};
        this.page.main.find(".ef-guide-loading").hide();
        this.page.main.find(".ef-guide-progress strong").text(`${this.context.progress || 0}%`);
        this.page.main.find(".ef-guide-progress span").text(__("{0} of {1} setup steps", [this.context.completed_steps || 0, this.context.total_steps || 0]));
        this.render_section();
    }

    render_section() {
        if (!this.context) return;
        const renderers = {
            start: () => this.render_start(),
            playbooks: () => this.render_playbooks(),
            accounting: () => this.render_accounting(),
            roles: () => this.render_roles(),
            help: () => this.render_help(),
        };
        renderers[this.active_section]();
    }

    render_start() {
        const modes = (this.context.enabled_modes || []).map((mode) => `<span class="ef-mode-chip">${frappe.utils.escape_html(mode.label)}</span>`).join("");
        const checklist = (this.context.checklist || []).map((item, index) => `
            <article class="ef-check-item ${item.complete ? "complete" : ""}">
                <span class="ef-check-icon">${item.complete ? "✓" : index + 1}</span>
                <div><h4>${frappe.utils.escape_html(item.label)}</h4><p>${frappe.utils.escape_html(item.description)}</p>
                ${item.detail ? `<small>${frappe.utils.escape_html(item.detail)}</small>` : ""}</div>
                <button class="btn btn-sm ${item.complete ? "btn-default" : "btn-primary"}" data-route="${frappe.utils.escape_html(item.route)}">${frappe.utils.escape_html(item.action)}</button>
            </article>`).join("");
        this.content(`
            <section class="ef-guide-grid two">
                <article class="ef-guide-card ef-setup-explainer">
                    <span class="ef-eyebrow">${__("WHAT RUN SETUP MEANS")}</span><h3>${__("Setup prepares safe defaults; it does not invent your properties")}</h3>
                    <p>${__("Running setup saves your company and business modes, copies company currency and default accounts, creates standard non-stock billing Items, and optionally creates one portfolio. It can be run again safely: existing Items and portfolios are not duplicated.")}</p>
                    <h4>${__("Setup changes")}</h4>
                    <ul><li>${__("EstateFlow Settings business-mode switches")}</li><li>${__("Default company, country, currency and cost centre")}</li><li>${__("Eight service Items for rent, accommodation, utilities, sales and commission")}</li><li>${__("One initial portfolio when selected")}</li><li>${__("Mode-aware guide and Command Center shortcuts")}</li></ul>
                    <h4>${__("Setup does not change")}</h4>
                    <ul><li>${__("It does not create houses, rooms, tenants or bookings")}</li><li>${__("It does not choose tax, withholding or statutory accounts")}</li><li>${__("It does not post invoices, journals or payments")}</li><li>${__("It does not delete records when a mode is disabled")}</li></ul>
                    <button class="btn btn-primary ef-run-setup">${__("Run or update guided setup")}</button>
                </article>
                <article class="ef-guide-card">
                    <span class="ef-eyebrow">${__("YOUR CONFIGURATION")}</span><h3>${frappe.utils.escape_html(this.context.company || __("No company selected"))}</h3>
                    <p>${__("Currency")}: <b>${frappe.utils.escape_html(this.context.currency || "—")}</b> · ${__("Property label")}: <b>${frappe.utils.escape_html(this.context.property_label || "Property")}</b></p>
                    <div class="ef-mode-list">${modes || `<span class="ef-mode-chip muted">${__("No business modes enabled")}</span>`}</div>
                    <div class="ef-mini-stats">
                        ${this.stat(this.context.counts?.portfolios, __("Portfolios"))}${this.stat(this.context.counts?.properties, __("Properties"))}${this.stat(this.context.counts?.spaces, __("Spaces"))}${this.stat(this.context.counts?.agreements, __("Agreements"))}
                    </div>
                    <p class="ef-note">${__("Business modes focus the onboarding and suggested workflows. All EstateFlow records remain available so a mixed business can operate hotels, rentals, sales and housing together.")}</p>
                </article>
            </section>
            <section class="ef-guide-card"><span class="ef-eyebrow">${__("GO-LIVE CHECKLIST")}</span><h3>${__("Complete these steps in order")}</h3><div class="ef-checklist">${checklist}</div></section>
            <section class="ef-guide-card ef-data-model"><span class="ef-eyebrow">${__("THE FIVE RECORDS TO UNDERSTAND")}</span><h3>${__("How EstateFlow organizes the business")}</h3>
                <div class="ef-model-flow"><b>${__("Company")}</b><i>→</i><b>${__("Portfolio")}</b><i>→</i><b>${__("Property")}</b><i>→</i><b>${__("Space")}</b><i>→</i><b>${__("Transaction")}</b></div>
                <div class="ef-model-notes"><p><b>${__("Property")}</b> — one house, hotel, lodge, apartment block, housing scheme, shopping centre or development.</p><p><b>${__("Space")}</b> — the bookable/rentable/sellable inventory: room, house, apartment, shop, office, bed, plot or parking space.</p><p><b>${__("Transaction")}</b> — a booking, occupancy agreement, sale contract, housing allocation or work order.</p></div>
            </section>`);
    }

    stat(value, label) { return `<div><strong>${format_number(value || 0)}</strong><span>${label}</span></div>`; }

    render_playbooks() {
        const books = this.playbooks();
        const enabled = new Set((this.context.enabled_modes || []).map((mode) => mode.key));
        const tabs = Object.entries(books).map(([key, book], index) => `<button data-playbook="${key}" class="${index === 0 ? "active" : ""}">${frappe.utils.escape_html(book.title)}${enabled.has(book.mode) ? `<small>✓ ${__("Enabled")}</small>` : ""}</button>`).join("");
        this.content(`<section class="ef-guide-card"><span class="ef-eyebrow">${__("BUSINESS PLAYBOOKS")}</span><h3>${__("Select the business you want to operate")}</h3><p>${__("Each playbook shows the minimum master data, exact daily process and ERPNext accounting result.")}</p><div class="ef-playbook-layout"><aside class="ef-playbook-tabs">${tabs}</aside><div class="ef-playbook-body"></div></div></section>`);
        this.render_playbook(Object.keys(books)[0]);
    }

    render_playbook(key) {
        const target = this.page.main.find(".ef-playbook-body");
        if (!target.length) return;
        const book = this.playbooks()[key];
        const steps = book.steps.map((step, index) => `<article class="ef-process-step"><span>${index + 1}</span><div><h4>${frappe.utils.escape_html(step[0])}</h4><p>${frappe.utils.escape_html(step[1])}</p>${step[2] ? `<button data-route="${step[2]}">${__("Open")}</button>` : ""}</div></article>`).join("");
        target.html(`<span class="ef-eyebrow">${frappe.utils.escape_html(book.tag)}</span><h2>${frappe.utils.escape_html(book.title)}</h2><p>${frappe.utils.escape_html(book.intro)}</p>
            <div class="ef-prereq"><b>${__("Create first")}</b><span>${frappe.utils.escape_html(book.create)}</span></div>
            <div class="ef-process-list">${steps}</div>
            <div class="ef-outcome"><b>${__("Accounting result")}</b><p>${frappe.utils.escape_html(book.accounting)}</p></div>
            <div class="ef-warning"><b>${__("Important")}</b><p>${frappe.utils.escape_html(book.note)}</p></div>`);
    }

    playbooks() {
        return {
            landlord: { mode: "landlord", title: __("Individual landlord"), tag: __("ONE HOUSE TO LARGE PORTFOLIO"), intro: __("Use this when you own houses or apartments and collect recurring rent."), create: __("Portfolio → Property → one Space for each separately rented house or apartment → Customer"), accounting: __("Submitting the agreement activates occupancy. Scheduled billing creates standard Sales Invoices; Payment Entry records collection. Deposits post to the configured liability account."), note: __("A house rented as one unit should be one Property with one Space. An apartment block should be one Property with many apartment Spaces."), steps: [[__("Add property"), __("Choose Residential and Owner Operated. Map its cost centre and income account."), "List/Real Estate Property"], [__("Add unit or house space"), __("Mark it rentable, available and set monthly base rent."), "List/Property Space"], [__("Create tenant Customer"), __("Use the standard ERPNext Customer and Contact records."), "List/Customer"], [__("Create occupancy agreement"), __("Select term, monthly frequency and add Base Rent plus any service charges."), "List/Occupancy Agreement"], [__("Record deposit and bill"), __("Use Security Deposit Transaction, then create or schedule Sales Invoices."), "List/Security Deposit Transaction"], [__("Collect and maintain"), __("Use Payment Entry for rent and Maintenance Request for tenant issues."), "List/Maintenance Request"]] },
            hotel: { mode: "hospitality", title: __("Hotel or lodge"), tag: __("RESERVATION TO HOUSEKEEPING"), intro: __("Use this for hotels, lodges, guest houses and serviced short-stay properties."), create: __("Hospitality portfolio → Hotel/Lodge Property → one bookable Space per room/villa → Customer"), accounting: __("The reservation folio creates a Sales Invoice for nights and extra charges. Checkout releases the room and can mark it Dirty for housekeeping."), note: __("EstateFlow currently provides direct reservations and operations. Channel-manager synchronization and advanced rate plans are future extensions."), steps: [[__("Create hotel or lodge"), __("Select Hotel or Lodge property type and define check-in/out defaults."), "List/Real Estate Property"], [__("Create rooms"), __("Use Hotel Room/Lodge Room, enable Short Stay, set capacity, nightly rate and Clean status."), "List/Property Space"], [__("Check availability"), __("Use the Availability Register or create a reservation; overlapping dates are blocked."), "query-report/Availability Register"], [__("Reserve and confirm"), __("Enter guest, dates, adults/children, source, room rate and optional charges."), "List/Property Reservation"], [__("Check in and invoice"), __("Use the contextual buttons. The room becomes Occupied and the folio becomes a Sales Invoice."), "List/Property Reservation"], [__("Check out and clean"), __("Checkout makes the room Available/Dirty; complete a Housekeeping Work Order to mark it Clean."), "List/Property Work Order"]] },
            agent: { mode: "brokerage", title: __("Sales and rental agent"), tag: __("LISTING TO COMMISSION"), intro: __("Use this when you market properties for owners and close rental or sale deals."), create: __("Owner Customer → Property/Space → Property Listing → Sales Partner or agent User"), accounting: __("Rental deals become occupancy agreements; sale deals become sale contracts. Approved supplier commissions create Purchase Invoices."), note: __("Use Sales Partner for an agency, User for an internal agent and Supplier when commission will be paid through Accounts Payable."), steps: [[__("Register inventory and owner"), __("Create the owner, property and sellable/rentable space."), "List/Property Space"], [__("Publish listing"), __("Choose rent, sale or short stay; enter price, validity, channel and commission."), "List/Property Listing"], [__("Capture enquiry"), __("Record requirements, source, budget and assigned agent."), "List/Property Enquiry"], [__("Schedule viewing"), __("Record date, agent, visitor feedback and next action."), "List/Viewing Appointment"], [__("Submit and accept offer"), __("Accepted offers can create a reservation/hold so the space is protected."), "List/Property Offer"], [__("Close and pay commission"), __("Convert to agreement/sale and create Real Estate Commission when earned."), "List/Real Estate Commission"]] },
            housing: { mode: "housing_authority", title: __("National or social housing"), tag: __("APPLICATION TO ALLOCATION"), intro: __("Use this for public housing, social rentals, staff housing, student housing and affordable purchase schemes."), create: __("National Housing portfolio → Scheme Property → allocatable unit/plot Spaces → applicant Customer"), accounting: __("Rental allocation converts to a recurring occupancy agreement. Purchase allocation converts to a sale contract and installment invoices."), note: __("EstateFlow stores eligibility evidence but deliberately does not impose a government policy formula. Configure the approved policy and committee workflow locally."), steps: [[__("Create housing scheme"), __("Use Social Housing/Staff Housing/Student Housing and Public/Government ownership."), "List/Real Estate Property"], [__("Load units or plots"), __("Mark spaces allocatable; also mark rentable or sellable according to the program."), "List/Property Space"], [__("Capture application"), __("Record identity, household, dependants, income, needs, documents and preferences."), "List/Housing Application"], [__("Review eligibility"), __("Set result and waitlist/eligible status according to approved policy."), "List/Housing Application"], [__("Approve allocation"), __("Select an available unit, allocation type, dates, amount and approving officer."), "List/Property Allocation"], [__("Convert and collect"), __("Create the tenancy or sale contract and use ERPNext invoices and payments."), "List/Property Allocation"]] },
            developer: { mode: "developer_sales", title: __("Property developer"), tag: __("UNIT SALE AND INSTALLMENTS"), intro: __("Use this for apartments, plots and development inventory sold before or after completion."), create: __("Development portfolio → Development Property → one sellable Space per unit/plot → buyer Customer"), accounting: __("Each due installment creates a Sales Invoice linked to the property, space and sale contract. Payment status follows invoice outstanding amount."), note: __("Select the income/revenue-recognition accounts according to your accountant's approved policy; EstateFlow does not choose IFRS/local recognition rules automatically."), steps: [[__("Create development inventory"), __("Create each apartment, villa or plot as a sellable Space with sale price."), "List/Property Space"], [__("List and receive enquiry"), __("Use listings, viewings and offers to manage the funnel."), "List/Property Enquiry"], [__("Reserve the unit"), __("Create a Property Sale Hold to prevent a second sale."), "List/Property Reservation"], [__("Create sale contract"), __("Contract value must equal installment total; percentages must total 100% when used."), "List/Property Sale Contract"], [__("Bill milestones"), __("The scheduler or action creates due Sales Invoices without duplicates."), "List/Sales Invoice"], [__("Complete handover"), __("After payment, record actual handover/title reference and mark the contract completed."), "List/Property Sale Contract"]] },
            manager: { mode: "property_management", title: __("Property management company"), tag: __("LEASES, COLLECTIONS AND FACILITIES"), intro: __("Use this when one team operates many properties, including properties managed for owners."), create: __("Managed portfolio → properties with Owner Customer → spaces → tenants and suppliers"), accounting: __("Property/cost-centre references flow into invoices, payments, purchasing and stock documents so ERPNext reports can be filtered by property."), note: __("Advanced owner trust statements and automated owner disbursement are planned. Until enabled, use approved ERPNext accounting dimensions and separate bank/trust controls."), steps: [[__("Register owner and portfolio"), __("Link Owner/Investor to the portfolio or property and assign managers."), "List/Property Portfolio"], [__("Load properties and units"), __("Map cost centres, projects, warehouses and property accounts."), "List/Real Estate Property"], [__("Operate leases"), __("Create agreements, deposits, recurring invoices, renewals and expiries."), "query-report/Rent Roll"], [__("Collect arrears"), __("Use Command Center and Accounts Receivable, then record Payment Entries."), "query-report/Accounts Receivable"], [__("Maintain properties"), __("Move requests through work orders, material requests and completion."), "List/Maintenance Request"], [__("Review performance"), __("Use property references plus ERPNext P&L, GL, receivable and buying reports."), "estateflow-command-center"]] },
            commercial: { mode: "property_management", title: __("Commercial, retail or warehouse"), tag: __("MULTI-CHARGE COMMERCIAL LEASING"), intro: __("Use for shops, offices, malls, industrial units and warehouses."), create: __("Commercial Property → shop/office/warehouse Spaces → tenant Customers"), accounting: __("Each agreement can bill rent, service charge, parking, insurance, utilities and management fees as separate Items/accounts."), note: __("Year-end CAM/service-charge reconciliation is a planned extension; current recurring billing supports periodic estimated charges."), steps: [[__("Create commercial inventory"), __("Define area, floor/zone, permitted use, rent and warehouse/cost-centre mappings."), "List/Property Space"], [__("Capture prospect and viewing"), __("Use enquiry, viewing and offer for controlled negotiation."), "List/Property Enquiry"], [__("Create commercial lease"), __("Add every recurring charge as a separate Agreement Charge row."), "List/Occupancy Agreement"], [__("Bill and collect"), __("Generate periodic invoices and allocate payments using standard ERPNext."), "List/Sales Invoice"], [__("Record meters"), __("Unit-level Utility Readings calculate consumption and can create invoices."), "List/Utility Reading"], [__("Manage facilities"), __("Track SLA, contractor, materials and property cost for each issue."), "List/Property Work Order"]] },
            community: { mode: "community", title: __("HOA, strata or community"), tag: __("SHARED PROPERTY OPERATIONS"), intro: __("Use this foundation for estates, condominium communities, owner associations and shared common facilities."), create: __("Community portfolio → Community/HOA Property → homes and Common Area Spaces → owner/occupant Customers"), accounting: __("Recurring association levies can be represented as HOA Levy Agreement Charges and billed through Sales Invoice. Common-area procurement carries the community property and cost-centre references."), note: __("Dedicated meetings, resolutions, violations, voting and statutory owner ledgers are planned extensions. Do not represent them as completed features in the current release."), steps: [[__("Create the community"), __("Select Community/HOA property type and Community Managed operating model."), "List/Real Estate Property"], [__("Register homes and common areas"), __("Create one Space per home plus pools, halls, gates and other maintained common areas."), "List/Property Space"], [__("Link owners and occupants"), __("Use Customer and Contact records; use occupancy agreements where recurring levies are billed."), "List/Customer"], [__("Configure levies"), __("Add HOA Levy as a recurring Agreement Charge using an approved service Item/account."), "List/Occupancy Agreement"], [__("Maintain common property"), __("Use inspections, maintenance requests and work orders for shared facilities."), "List/Maintenance Request"], [__("Review finances"), __("Use receivable, general ledger and buying reports filtered by community property/cost centre."), "query-report/Accounts Receivable"]] },
            investment: { mode: "investment", title: __("Investment portfolio or REIT"), tag: __("PROPERTY-LEVEL FINANCIAL CONTROL"), intro: __("Use this for a portfolio where management needs income, expenses, occupancy and investment performance by property."), create: __("Investment Fund portfolio → income-producing Properties → Spaces → property cost centres/projects"), accounting: __("Sales and purchase documents carry EstateFlow property references while ERPNext cost centres/projects provide auditable P&L, balance-sheet and cash-flow analysis."), note: __("Advanced valuation, investor-unit registry, distribution waterfall and statutory REIT reporting are planned. Current reports provide the accounting and occupancy foundation, not a complete regulated fund register."), steps: [[__("Create investment portfolio"), __("Use Investment Fund type and identify the owner/investor Customer where appropriate."), "List/Property Portfolio"], [__("Map accounting dimensions"), __("Give every property its approved cost centre, project, income, expense and warehouse defaults."), "List/Real Estate Property"], [__("Operate income contracts"), __("Use agreements, reservations and sale contracts so every invoice links back to the asset."), "query-report/Rent Roll"], [__("Capture property expenditure"), __("Use EstateFlow-linked Purchase Invoices, work orders and stock documents."), "List/Purchase Invoice"], [__("Review occupancy and cash collection"), __("Use Command Center, Rent Roll, receivables and lease-expiry reports."), "estateflow-command-center"], [__("Review financial performance"), __("Use ERPNext P&L, GL and cash-flow reports by cost centre/project; apply locally approved NOI/cap-rate analysis."), "query-report/Profit and Loss Statement"]] },
            facilities: { mode: "property_management", title: __("Facilities and maintenance"), tag: __("REQUEST TO PROCUREMENT"), intro: __("Use this flow for corrective, preventive, housekeeping, turnover and inspection work."), create: __("Property/Space → maintenance teams and Supplier contractors → stock Items and Warehouses"), accounting: __("Work Order creates a Material Request; ERPNext continues through RFQ, quotation, Purchase Order, receipt, Purchase Invoice and Payment."), note: __("Submit work orders only after assignment and scope approval. Configure buying roles and warehouses before requesting material."), steps: [[__("Report issue"), __("Record category, priority, source, description, photos and SLA."), "List/Maintenance Request"], [__("Create work order"), __("Assign internal technician or Supplier, schedule work and add materials."), "List/Property Work Order"], [__("Request material"), __("Generate an ERPNext Material Request carrying property and work-order references."), "List/Material Request"], [__("Buy or issue stock"), __("Continue through standard RFQ/PO/Receipt or Stock Entry."), "List/Purchase Order"], [__("Complete and verify"), __("Record completion notes, actual dates and housekeeping result."), "List/Property Work Order"], [__("Analyze"), __("Review open requests, SLA breaches and purchasing cost by property."), "estateflow-command-center"]] },
        };
    }

    render_accounting() {
        this.content(`<section class="ef-guide-grid two"><article class="ef-guide-card"><span class="ef-eyebrow">${__("REVENUE AND COLLECTION")}</span><h3>${__("Operational records create standard ERPNext accounting")}</h3>${this.flow([[__("Agreement / Reservation / Sale"), __("Defines who, what property and what amount")], [__("Sales Invoice"), __("Posts receivable and configured income")], [__("Payment Entry"), __("Clears customer outstanding balance")], [__("General Ledger"), __("Reports by company, cost centre and EstateFlow references")]])}</article>
            <article class="ef-guide-card"><span class="ef-eyebrow">${__("DEPOSIT CONTROL")}</span><h3>${__("Security deposits remain liabilities")}</h3>${this.flow([[__("Deposit receipt"), __("Debit bank/cash; credit deposit liability")], [__("Refund"), __("Debit liability; credit bank/cash")], [__("Apply to invoice"), __("Debit liability; credit customer receivable")], [__("Adjustment"), __("Debit liability; credit approved adjustment account")]])}<p class="ef-note">${__("Automated deposit journals currently require agreement currency to equal company currency.")}</p></article></section>
            <section class="ef-guide-card"><span class="ef-eyebrow">${__("SUPPLY CHAIN")}</span><h3>${__("Maintenance request to supplier payment")}</h3><div class="ef-horizontal-flow">${[__("Request"),__("Work Order"),__("Material Request"),__("RFQ"),__("Quotation"),__("Purchase Order"),__("Receipt / Stock"),__("Purchase Invoice"),__("Payment")].map((x,i)=>`<b>${x}</b>${i<8?"<i>→</i>":""}`).join("")}</div></section>
            <section class="ef-guide-card"><span class="ef-eyebrow">${__("BEFORE GO-LIVE")}</span><h3>${__("Accounting decisions EstateFlow will not make for you")}</h3><div class="ef-decision-grid">${[__("VAT/GST and withholding templates"),__("Security-deposit custody and approval policy"),__("Trust/escrow or owner-fund separation"),__("Property-sale revenue recognition"),__("Capitalization and depreciation"),__("Fiscal-device or e-invoice integration"),__("Foreign-currency exchange policy"),__("Local print and statutory formats")].map(x=>`<span>□ ${x}</span>`).join("")}</div><button class="btn btn-primary" data-route="Form/EstateFlow Settings/EstateFlow Settings">${__("Review account mappings")}</button></section>`);
    }

    flow(rows) { return `<div class="ef-account-flow">${rows.map((row,index)=>`<div><span>${index+1}</span><p><b>${row[0]}</b><small>${row[1]}</small></p></div>`).join("")}</div>`; }

    render_roles() {
        const roles = [[__("EstateFlow Administrator"),__("Setup, permissions, all EstateFlow masters and transactions")],[__("Portfolio Manager"),__("Portfolio performance, properties and management oversight")],[__("Property Manager"),__("Properties, occupancy, maintenance and daily operational control")],[__("Leasing Officer"),__("Enquiries, offers, agreements, deposits and renewals")],[__("Estate Agent"),__("Listings, viewings, offers, sales and commissions")],[__("Front Desk Officer"),__("Reservations, guest details, check-in, invoices and checkout")],[__("Housing Officer"),__("Applications, eligibility evidence, allocations and conversion")],[__("Facilities Officer"),__("Requests, inspections, work orders, utilities and materials")],[__("Accounts roles"),__("Invoices, journals, deposits, payments, payables and financial reports")]];
        this.content(`<section class="ef-guide-card"><span class="ef-eyebrow">${__("ROLE-BASED WORK")}</span><h3>${__("Give each user only the work they need")}</h3><div class="ef-role-grid">${roles.map(row=>`<article><b>${row[0]}</b><p>${row[1]}</p></article>`).join("")}</div><p class="ef-note">${__("EstateFlow roles control custom records. Standard ERPNext Accounts, Sales, Purchase and Stock roles still control their documents. Review Company and User Permissions before production use.")}</p></section>
            <section class="ef-guide-grid three">${[[__("Every morning"),__("Review arrivals, arrears, expiring leases and SLA breaches on Command Center.")],[__("During the day"),__("Use contextual buttons on each record; actions appear only when valid for the current status.")],[__("End of day"),__("Confirm invoices/payments, unresolved emergencies, dirty rooms and pending procurement approvals.")]].map(row=>`<article class="ef-guide-card"><h3>${row[0]}</h3><p>${row[1]}</p></article>`).join("")}</section>`);
    }

    render_help() {
        const questions = [[__("I ran setup but the dashboard is still zero"),__("Setup does not create business data. Complete the checklist: create a Property, then at least one Space, Customer and transaction. Dashboard numbers are live totals, not demonstration data.")],[__("What is a Property versus a Space?"),__("Property is the location/business asset; Space is the inventory being rented, booked, sold or allocated. A hotel is a Property and each room is a Space.")],[__("Why can I not book or lease a unit?"),__("The Space must be Ready, enabled for the intended use and free of overlapping reservations/agreements. Sold, blocked and owner-occupied spaces cannot be booked.")],[__("Why was no invoice created?"),__("The source document must be submitted, a valid Customer and service Item must exist, account mappings must be valid and the billing date must be due.")],[__("Why is a room available but dirty?"),__("Occupancy and housekeeping are separate. Checkout can release occupancy while marking the room Dirty. Complete a Housekeeping Work Order before the next guest.")],[__("Why do I still see modules I did not enable?"),__("Business modes focus setup and recommendations; they do not delete or lock records. This permits one company to add another real-estate business without reinstalling the app.")],[__("Where are payments and the general ledger?"),__("EstateFlow uses standard ERPNext Sales Invoice, Purchase Invoice, Payment Entry and Journal Entry. Use ERPNext accounting reports rather than a duplicate property ledger.")],[__("Can setup be run more than once?"),__("Yes. It updates settings and creates only missing standard Items/portfolio. Existing property and transaction records are not deleted.")]];
        this.content(`<section class="ef-guide-card"><span class="ef-eyebrow">${__("COMMON QUESTIONS")}</span><h3>${__("Understand what the system is doing")}</h3><div class="ef-faq">${questions.map((row,index)=>`<details ${index===0?"open":""}><summary>${row[0]}</summary><p>${row[1]}</p></details>`).join("")}</div></section>
            <section class="ef-guide-grid three"><article class="ef-guide-card"><h3>${__("System setup")}</h3><p>${__("Company, modes, defaults and accounts.")}</p><button data-route="Form/EstateFlow Settings/EstateFlow Settings">${__("Open settings")}</button></article><article class="ef-guide-card"><h3>${__("Operational status")}</h3><p>${__("Live occupancy, billing and attention items.")}</p><button data-route="estateflow-command-center">${__("Command Center")}</button></article><article class="ef-guide-card"><h3>${__("Product documentation")}</h3><p>${__("The repository README contains installation, architecture and API details.")}</p><button data-route="Workspace/EstateFlow">${__("EstateFlow workspace")}</button></article></section>`);
    }

    content(html) { this.page.main.find(".ef-guide-content").html(html); }

    async show_setup() {
        const stateResponse = await frappe.call("estateflow.api.setup.get_setup_state");
        const state = stateResponse.message || {};
        const current = state.settings || {};
        const dialog = new frappe.ui.Dialog({
            title: __("EstateFlow Guided Setup"), size: "large", fields: [
                { fieldtype: "HTML", fieldname: "explanation", options: `<div class="ef-setup-intro"><span>✦</span><div><h3>${__("Prepare defaults—not demonstration data")}</h3><p>${__("This saves business modes and creates safe service masters. The checklist will then guide you to create real properties and transactions.")}</p></div></div>` },
                { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1, default: current.company || state.companies?.[0]?.name },
                { fieldname: "property_label", label: __("Familiar property label"), fieldtype: "Select", options: "Property\nEstate\nHotel\nLodge\nHousing Scheme\nDevelopment", default: current.property_label || "Property" },
                { fieldtype: "Section Break", label: __("Enable every business you operate") },
                ...this.mode_fields(current),
                { fieldtype: "Section Break", label: __("Safe records setup may create") },
                { fieldname: "create_standard_items", label: __("Create missing standard billing Items"), fieldtype: "Check", default: 1, description: __("No stock and no opening balances are created.") },
                { fieldname: "create_initial_portfolio", label: __("Create an initial portfolio if missing"), fieldtype: "Check", default: 1 },
            ],
            primary_action_label: __("Apply setup and show changes"),
            primary_action: async (values) => {
                const keys = ["landlord","property_management","housing_authority","developer_sales","brokerage","hospitality","community","investment"];
                const selected = keys.filter((key) => values[key]);
                if (!selected.length) { frappe.msgprint(__("Enable at least one business mode.")); return; }
                const result = await frappe.call({ method: "estateflow.api.setup.complete_setup", args: { company: values.company, business_modes: JSON.stringify(selected), property_label: values.property_label, create_standard_items: values.create_standard_items, create_initial_portfolio: values.create_initial_portfolio }, freeze: true, freeze_message: __("Applying EstateFlow setup…") });
                const out = result.message || {};
                dialog.hide();
                frappe.msgprint({ title: __("Setup applied"), indicator: "green", message: `<p><b>${__("Enabled modes")}:</b> ${selected.map(x=>__(x.replaceAll("_"," "))).join(", ")}</p><p><b>${__("New Items created")}:</b> ${(out.created_items || []).length ? out.created_items.join(", ") : __("None; standard Items already existed or creation was disabled")}</p><p><b>${__("Portfolio")}:</b> ${out.portfolio || __("Not created")}</p><p>${__("No properties, rooms, tenants, bookings or invoices were created. Continue with the checklist.")}</p>` });
                await this.refresh();
            },
        });
        dialog.show();
    }

    mode_fields(current) {
        const rows = [
            ["landlord", __("Houses and long-term rentals"), "enable_landlord"], ["property_management", __("Manage properties for owners"), "enable_property_management"], ["housing_authority", __("National or social housing"), "enable_housing_authority"], ["developer_sales", __("Developments and unit sales"), "enable_developer_sales"],
            ["column", "", ""], ["brokerage", __("Agent sales and rentals"), "enable_brokerage"], ["hospitality", __("Hotel, lodge or short stay"), "enable_hospitality"], ["community", __("HOA, strata or community"), "enable_community"], ["investment", __("Investment portfolio or REIT"), "enable_investment"],
        ];
        return rows.map((row) => row[0] === "column" ? { fieldtype: "Column Break" } : { fieldname: row[0], label: row[1], fieldtype: "Check", default: current[row[2]] ? 1 : 0 });
    }
}
