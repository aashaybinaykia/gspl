// Copyright (c) 2023, GSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Case Detail Transfer', {
	onload: function(frm) {
		if (frm.is_new()) {
			frm.set_value('stock_entry', '')
		}
	},

	from_warehouse: function(frm) {
		$.each(frm.doc.items || [], function(idx, d) {
			frappe.model.set_value(d.doctype, d.name, 'source_warehouse', frm.doc.from_warehouse);
		})
	},

	to_warehouse: function(frm) {
		$.each(frm.doc.items || [], function(idx, d) {
			frappe.model.set_value(d.doctype, d.name, 'target_warehouse', frm.doc.to_warehouse);
		})
	},
});
