// Sales Invoice

frappe.ui.form.on('Sales Invoice Item', {
	stock_uom_rate(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
        let rate = flt(row.stock_uom_rate) * flt(row.conversion_factor);

        frappe.model.set_value(cdt, cdn, "rate", rate);
	}
})
