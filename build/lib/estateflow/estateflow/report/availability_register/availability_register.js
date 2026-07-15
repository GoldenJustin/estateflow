frappe.query_reports["Availability Register"] = {
    filters: [
        { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", default: frappe.defaults.get_user_default("Company") },
        { fieldname: "property", label: __("Property"), fieldtype: "Link", options: "Real Estate Property", get_query: () => ({ filters: { company: frappe.query_report.get_filter_value("company") } }) },
        { fieldname: "space_type", label: __("Space Type"), fieldtype: "Select", options: "\nHouse\nApartment\nVilla\nRoom\nBed\nHotel Room\nLodge Room\nShop\nOffice\nWarehouse\nIndustrial Unit\nLand Plot\nParking\nStorage\nDesk\nOther" },
        { fieldname: "occupancy_status", label: __("Occupancy"), fieldtype: "Select", options: "\nAvailable\nReserved\nOccupied\nUnder Contract\nSold\nOwner Occupied\nBlocked" },
        { fieldname: "use", label: __("Use"), fieldtype: "Select", options: "\nLong-term Rent\nSale\nShort Stay\nHousing Allocation" },
    ],
    formatter(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        if (column.fieldname === "occupancy_status") {
            const colors = { Available: "green", Reserved: "orange", Occupied: "blue", "Under Contract": "purple", Sold: "grey", Blocked: "red" };
            return `<span class="indicator-pill ${colors[data.occupancy_status] || "grey"}">${value}</span>`;
        }
        return value;
    },
};
