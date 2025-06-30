frappe.listview_settings["Trip Status"] = {
	add_fields: ["colour"],
	formatters: {
		colour: function (value) {
			if (value) {
				return `<span class="indicator-pill ${value} filterable no-indicator-dot ellipsis">
					<span class="ellipsis">${__(value)}</span>
				</span>`;
			}
			return value;
		},
	},
};
