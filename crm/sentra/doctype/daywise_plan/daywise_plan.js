// Copyright (c) 2025, arvis and contributors
// For license information, please see license.txt

frappe.ui.form.on("Daywise Plan", {
	refresh(frm) {},
});

frappe.ui.form.on("Quote", {
	costadult(frm, cdt, cdn) {
		update_total_amount(frm);
	},
	costchild(frm, cdt, cdn) {
		update_total_amount(frm);
	},
	quotes_remove(frm, cdt, cdn) {
		// Also update total if a row is removed
		update_total_amount(frm);
	},
	items_remove(frm) {
		update_total_amount(frm);
	},
});

function update_total_amount(frm) {
	let total = 0;

	(frm.doc.items || []).forEach((row) => {
		total += (row.costadult || 0) + (row.costchild || 0);
	});
	// Set total_amount on parent (Daywise Plan)
	frm.set_value("total_amount", total);
}
