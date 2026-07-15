function ensure_estateflow_command_center_styles() {
    const stylesheetId = "estateflow-command-center-styles";
    if (document.getElementById(stylesheetId)) return;

    const link = document.createElement("link");
    link.id = stylesheetId;
    link.rel = "stylesheet";
    link.type = "text/css";
    link.href = "/assets/estateflow/css/estateflow.css?v=0.1.4";
    document.head.appendChild(link);
}

frappe.pages["estateflow-command-center"].on_page_load = function (wrapper) {
    // Frappe v16 can retain a pre-install Desk shell that does not yet contain
    // a newly installed app's app_include_css entry. Load the page stylesheet
    // explicitly as well; the fixed id prevents duplicate requests.
    ensure_estateflow_command_center_styles();
    frappe.estateflow_command_center = new EstateFlowCommandCenter(wrapper);
};

frappe.pages["estateflow-command-center"].on_page_show = function () {
    if (frappe.estateflow_command_center) frappe.estateflow_command_center.refresh();
};

class EstateFlowCommandCenter {
    constructor(wrapper) {
        this.wrapper = $(wrapper);
        this.page = frappe.ui.make_app_page({
            parent: wrapper,
            title: __("EstateFlow"),
            single_column: true,
        });
        this.filters = {};
        this.make_filters();
        this.make_shell();
        this.bind_actions();
        this.check_setup();
    }

    make_filters() {
        this.company = this.page.add_field({
            label: __("Company"), fieldtype: "Link", options: "Company", fieldname: "company",
            change: () => { this.property.set_value(""); this.refresh(); },
        });
        this.property = this.page.add_field({
            label: __("Property"), fieldtype: "Link", options: "Real Estate Property", fieldname: "property",
            get_query: () => ({ filters: this.company.get_value() ? { company: this.company.get_value() } : {} }),
            change: () => this.refresh(),
        });
        this.from_date = this.page.add_field({
            label: __("From"), fieldtype: "Date", fieldname: "from_date",
            default: frappe.datetime.add_days(frappe.datetime.get_today(), -30), change: () => this.refresh(),
        });
        this.to_date = this.page.add_field({
            label: __("To"), fieldtype: "Date", fieldname: "to_date",
            default: frappe.datetime.get_today(), change: () => this.refresh(),
        });
        this.page.set_primary_action(__("New"), () => this.show_create_menu(), "add");
        this.page.add_menu_item(__("Run Setup"), () => this.show_setup_dialog());
        this.page.add_menu_item(__("Guide & Business Playbooks"), () => frappe.set_route("estateflow-guide"));
        this.page.add_menu_item(__("Refresh"), () => this.refresh(), true);
    }

    make_shell() {
        this.page.main.addClass("estateflow-command-center").html(`
            <section class="ef-hero">
                <div>
                    <span class="ef-eyebrow">${__("LIVE PORTFOLIO COMMAND CENTER")}</span>
                    <h2>${__("Everything that needs attention, in one place.")}</h2>
                    <p>${__("Move from occupancy to collections, arrivals, sales and maintenance without leaving this page.")}</p>
                </div>
                <div class="ef-hero-actions">
                    <button class="btn btn-light ef-route" data-route="estateflow-guide">${__("Guide & setup")}</button>
                    <button class="btn btn-light ef-quick" data-doctype="Property Reservation">${__("New booking")}</button>
                    <button class="btn btn-light ef-quick" data-doctype="Occupancy Agreement">${__("New lease")}</button>
                    <button class="btn btn-light ef-quick" data-doctype="Maintenance Request">${__("Report issue")}</button>
                </div>
            </section>
            <div class="ef-loading">${__("Loading your portfolio…")}</div>
            <section class="ef-kpi-grid"></section>
            <section class="ef-main-grid">
                <article class="ef-panel ef-space-panel">
                    <header><div><span class="ef-eyebrow">${__("INVENTORY")}</span><h3>${__("Space status")}</h3></div>
                    <a class="ef-route" data-route="query-report/Availability Register">${__("Open availability")}</a></header>
                    <div class="ef-space-status"></div>
                </article>
                <article class="ef-panel ef-attention-panel">
                    <header><div><span class="ef-eyebrow">${__("ATTENTION")}</span><h3>${__("Operational pulse")}</h3></div></header>
                    <div class="ef-activity"></div>
                </article>
            </section>
            <section class="ef-panel ef-upcoming-panel">
                <header><div><span class="ef-eyebrow">${__("NEXT UP")}</span><h3>${__("Upcoming arrivals and expiries")}</h3></div>
                <span class="ef-generated"></span></header>
                <div class="ef-upcoming"></div>
            </section>
            <section class="ef-shortcuts">
                <button class="ef-shortcut ef-quick" data-doctype="Property Enquiry"><span>01</span><b>${__("Capture enquiry")}</b><small>${__("Rent, buy, stay or housing")}</small></button>
                <button class="ef-shortcut ef-quick" data-doctype="Viewing Appointment"><span>02</span><b>${__("Schedule viewing")}</b><small>${__("Assign an agent instantly")}</small></button>
                <button class="ef-shortcut ef-quick" data-doctype="Housing Application" data-mode="housing_authority"><span>03</span><b>${__("Housing application")}</b><small>${__("Eligibility and allocation")}</small></button>
                <button class="ef-shortcut ef-quick" data-doctype="Utility Reading"><span>04</span><b>${__("Record meter")}</b><small>${__("Calculate and bill usage")}</small></button>
            </section>
        `);
    }

    bind_actions() {
        this.page.main.on("click", ".ef-route", (event) => {
            const route = $(event.currentTarget).data("route");
            if (route) frappe.set_route(route.split("/"));
        });
        this.page.main.on("click", ".ef-quick", (event) => {
            const doctype = $(event.currentTarget).data("doctype");
            if (doctype) frappe.new_doc(doctype, this.route_defaults());
        });
        this.page.main.on("click", ".ef-open-doc", (event) => {
            const target = $(event.currentTarget);
            frappe.set_route("Form", target.data("doctype"), target.data("name"));
        });
    }

    route_defaults() {
        const values = {};
        if (this.company.get_value()) values.company = this.company.get_value();
        if (this.property.get_value()) values.property = this.property.get_value();
        return values;
    }

    show_create_menu() {
        const dialog = new frappe.ui.Dialog({
            title: __("What would you like to do?"),
            fields: [{ fieldtype: "HTML", fieldname: "actions", options: `
                <div class="ef-create-grid">
                    ${this.create_action("Property Reservation", __("Book a room or hold a unit"), "calendar")}
                    ${this.create_action("Occupancy Agreement", __("Create a tenancy or lease"), "file-text")}
                    ${this.create_action("Property Sale Contract", __("Start a property sale"), "trending-up")}
                    ${this.create_action("Property Enquiry", __("Capture a buyer, tenant or guest"), "users")}
                    ${this.create_action("Maintenance Request", __("Report maintenance"), "tool")}
                    ${this.create_action("Property Space", __("Add a house, room, unit or plot"), "home")}
                </div>` }],
        });
        dialog.$wrapper.on("click", ".ef-create-action", (event) => {
            dialog.hide();
            frappe.new_doc($(event.currentTarget).data("doctype"), this.route_defaults());
        });
        dialog.show();
    }

    create_action(doctype, description, icon) {
        return `<button class="ef-create-action" data-doctype="${frappe.utils.escape_html(doctype)}">
            <span class="ef-create-icon">${frappe.utils.icon(icon, "md")}</span><span><b>${__(doctype)}</b><small>${description}</small></span>
        </button>`;
    }

    async check_setup() {
        try {
            const response = await frappe.call("estateflow.api.setup.get_setup_state");
            const state = response.message || {};
            if (!state.configured) this.show_setup_dialog(state);
            else {
                if (!this.company.get_value()) this.company.set_value(state.settings.company);
                this.refresh();
            }
        } catch (error) {
            this.refresh();
        }
    }

    show_setup_dialog(state) {
        const dialog = new frappe.ui.Dialog({
            title: __("Welcome to EstateFlow"),
            size: "large",
            static: true,
            fields: [
                { fieldtype: "HTML", fieldname: "intro", options: `<div class="ef-setup-intro"><span>✦</span><div><h3>${__("One setup. Every property business.")}</h3><p>${__("Select what you operate today. You can enable more modes later.")}</p></div></div>` },
                { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", reqd: 1, default: state?.companies?.[0]?.name },
                { fieldname: "property_label", label: __("What do you call a property?"), fieldtype: "Select", options: "Property\nEstate\nHotel\nLodge\nHousing Scheme\nDevelopment", default: "Property" },
                { fieldtype: "Section Break", label: __("Your operations") },
                { fieldname: "landlord", label: __("Houses and long-term rentals"), fieldtype: "Check", default: 1 },
                { fieldname: "property_management", label: __("Manage properties for owners"), fieldtype: "Check", default: 1 },
                { fieldname: "housing_authority", label: __("National or social housing"), fieldtype: "Check" },
                { fieldname: "developer_sales", label: __("Developments and unit sales"), fieldtype: "Check" },
                { fieldtype: "Column Break" },
                { fieldname: "brokerage", label: __("Agent sales and rentals"), fieldtype: "Check" },
                { fieldname: "hospitality", label: __("Hotel, lodge or short stay"), fieldtype: "Check" },
                { fieldname: "community", label: __("HOA, strata or community"), fieldtype: "Check" },
                { fieldname: "investment", label: __("Investment portfolio or REIT"), fieldtype: "Check" },
                { fieldtype: "Section Break" },
                { fieldname: "create_standard_items", label: __("Create standard billing services"), fieldtype: "Check", default: 1 },
                { fieldname: "create_initial_portfolio", label: __("Create my first portfolio"), fieldtype: "Check", default: 1 },
            ],
            primary_action_label: __("Start using EstateFlow"),
            primary_action: async (values) => {
                const modes = Object.keys(frappe.estateflow_modes || {}).filter((key) => values[key]);
                // Keep the list explicit when this app is loaded without any global boot additions.
                const modeFields = ["landlord", "property_management", "housing_authority", "developer_sales", "brokerage", "hospitality", "community", "investment"];
                const selected = modeFields.filter((key) => values[key]);
                if (!selected.length) {
                    frappe.msgprint(__("Enable at least one business mode."));
                    return;
                }
                const setupResponse = await frappe.call({
                    method: "estateflow.api.setup.complete_setup",
                    args: {
                        company: values.company, business_modes: JSON.stringify(selected),
                        property_label: values.property_label,
                        create_standard_items: values.create_standard_items,
                        create_initial_portfolio: values.create_initial_portfolio,
                    },
                    freeze: true, freeze_message: __("Preparing your workspace…"),
                });
                const setupResult = setupResponse.message || {};
                dialog.hide();
                this.company.set_value(values.company);
                await this.refresh();
                frappe.msgprint({
                    title: __("EstateFlow setup applied"), indicator: "green",
                    message: `<p><b>${__("What changed")}</b></p>
                        <ul><li>${__("Company and {0} business mode(s) saved", [selected.length])}</li>
                        <li>${__("New billing Items created")}: ${(setupResult.created_items || []).length ? setupResult.created_items.join(", ") : __("none; they already existed or creation was disabled")}</li>
                        <li>${__("Portfolio")}: ${setupResult.portfolio || __("not created")}</li></ul>
                        <p><b>${__("What did not change")}</b></p><p>${__("Setup does not create properties, rooms, tenants, bookings or invoices. Open Guide & Setup and complete the go-live checklist.")}</p>`,
                    primary_action: { label: __("Open full guide"), action: () => frappe.set_route("estateflow-guide") },
                });
            },
        });
        dialog.show();
    }

    async refresh() {
        if (!this.page || this.loading) return;
        this.loading = true;
        this.page.main.find(".ef-loading").show();
        try {
            const response = await frappe.call({
                method: "estateflow.api.dashboard.get_command_center",
                args: {
                    company: this.company?.get_value(), property: this.property?.get_value(),
                    from_date: this.from_date?.get_value(), to_date: this.to_date?.get_value(),
                },
            });
            this.render(response.message || {});
        } finally {
            this.loading = false;
            this.page.main.find(".ef-loading").hide();
        }
    }

    render(data) {
        this.currency = data.currency || "";
        this.render_cards(data.cards || []);
        this.render_spaces(data.space_status || []);
        this.render_activity(data.activity || []);
        this.render_upcoming(data.upcoming || []);
        const modes = new Set(data.business_modes || []);
        this.page.main.find("[data-mode]").each((_, element) => {
            $(element).toggle(modes.has($(element).data("mode")));
        });
        this.page.main.find(".ef-generated").text(__("Updated {0}", [frappe.datetime.prettyDate(data.generated_at)]));
    }

    format_value(card) {
        if (card.format === "currency") return format_currency(card.value, this.currency);
        if (card.format === "percent") return `${flt(card.value, 1).toFixed(1)}%`;
        return format_number(card.value || 0);
    }

    render_cards(cards) {
        const html = cards.map((card) => `<button class="ef-kpi ef-route ef-tone-${card.tone || "slate"}" data-route="${frappe.utils.escape_html(card.route || "")}">
            <span class="ef-kpi-label">${frappe.utils.escape_html(card.label)}</span>
            <strong>${this.format_value(card)}</strong>
            <small>${frappe.utils.escape_html(card.subtext || __("Open details"))}</small>
        </button>`).join("");
        this.page.main.find(".ef-kpi-grid").html(html || this.empty_state(__("No metrics yet")));
    }

    render_spaces(statuses) {
        const total = statuses.reduce((sum, row) => sum + cint(row.value), 0) || 1;
        const html = statuses.map((row) => {
            const width = Math.max(2, cint(row.value) / total * 100);
            const slug = (row.label || "unknown").toLowerCase().replace(/\s/g, "-");
            return `<div class="ef-status-row"><div><span class="ef-dot ef-${slug}"></span><b>${frappe.utils.escape_html(__(row.label))}</b><span>${format_number(row.value)}</span></div>
                <div class="ef-status-track"><i class="ef-${slug}" style="width:${width}%"></i></div></div>`;
        }).join("");
        this.page.main.find(".ef-space-status").html(html || this.empty_state(__("Add your first unit, room or plot")));
    }

    render_activity(items) {
        const html = items.map((item) => `<button class="ef-activity-row ef-route" data-route="${frappe.utils.escape_html(item.route)}">
            <span class="ef-activity-icon">${frappe.utils.icon(item.icon || "circle", "sm")}</span>
            <span>${frappe.utils.escape_html(item.label)}</span><strong>${format_number(item.value)}</strong></button>`).join("");
        this.page.main.find(".ef-activity").html(html || this.empty_state(__("Nothing needs attention")));
    }

    render_upcoming(items) {
        const html = items.map((item) => `<button class="ef-upcoming-row ef-open-doc" data-doctype="${frappe.utils.escape_html(item.doctype)}" data-name="${frappe.utils.escape_html(item.name)}">
            <span class="ef-date-tile"><b>${frappe.datetime.str_to_user(item.date).split("-")[0]}</b><small>${frappe.datetime.str_to_user(item.date)}</small></span>
            <span class="ef-upcoming-copy"><small>${frappe.utils.escape_html(item.type)}</small><b>${frappe.utils.escape_html(item.title)}</b><em>${frappe.utils.escape_html(item.meta)}</em></span>
            <span>›</span></button>`).join("");
        this.page.main.find(".ef-upcoming").html(html || this.empty_state(__("No arrivals or expiries coming up")));
    }

    empty_state(message) {
        return `<div class="ef-empty"><span>✓</span><p>${frappe.utils.escape_html(message)}</p></div>`;
    }
}
