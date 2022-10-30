// Product Bundle

// Queries
cur_frm.set_query('batch_no', 'items', function(frm, cdt, cdn) {
    const row = locals[cdt][cdn];
    if(!cur_frm.doc.warehouse) {
        frappe.throw(__("Please select warehouse!"))
    }
    if(!row.item_code) {
        frappe.throw(__("Please select item code!"))
    }

    return {
        query: "erpnext.controllers.queries.get_batch_no",
        filters: {
            item_code: row.item_code,
            warehouse: cur_frm.doc.warehouse,
        },
    }
})

frappe.ui.form.on('Product Bundle', {
    before_save: function(frm) {
        frm.trigger('calculate_rate_and_qty')
    },

    calculate_qty_and_amt: function(frm) {
        // Calculates 'Total Qty' and 'Total Amount'
        let total_qty = frappe.utils.sum((frm.doc.items || []).map((d) => {return flt(d.qty)}));
        let total_amount = frappe.utils.sum((frm.doc.items || []).map((d) => {return flt(d.rate) * flt(d.qty)}));

        frm.set_value('total_qty', flt(total_qty))
        frm.set_value('total_amount', flt(total_amount))
    }
})


frappe.ui.form.on('Product Bundle Item', {
    qty: function(frm, cdt, cdn) {
        frm.events.calculate_qty_and_amt(frm)
    },

    rate: function(frm, cdt, cdn) {
        frm.events.calculate_qty_and_amt(frm)
    }
})
