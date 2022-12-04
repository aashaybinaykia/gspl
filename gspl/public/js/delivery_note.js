// Delivery Note

frappe.ui.form.on('Delivery Note', {
    before_save: function(frm) {
        $.each(frm.doc.items || [], function(idx, row) {
            if (row.batch_no){
                frappe.call({
                    method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
                    args: {
                        item_code: row.item_code,
                        warehouse: row.warehouse,
                        batch_no: row.batch_no, 
                    },
                    callback: (r) => {
                        if(!r.message) {
                            return;
                        }
                        let qty = r.message;

                        if (qty) {
                            frappe.model.set_value(row.doctype, row.name, "conversion_factor", qty);
                        }
                    }
                })
            }
        })
    },
})

frappe.ui.form.on('Delivery Note Item', {
    batch_no: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (row.batch_no){
            frappe.call({
                method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
                args: {
                    item_code: row.item_code,
                    warehouse: row.warehouse,
                    batch_no: row.batch_no, 
                },
                callback: (r) => {
                    if(!r.message) {
                        return;
                    }
                    let qty = r.message;

                    if (qty) {
                        setTimeout(() => {
                            frappe.model.set_value(cdt, cdn, "conversion_factor", qty);
                        }, 2000);
                    }
                }
            })
        }
    }
})
