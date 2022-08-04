// Copyright (c) 2022, GSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Bundle Transfer', {	
	onload: function(frm) {
		if (frm.is_new()) {
			frm.set_value('stock_entry', '')
		}
	}
});
