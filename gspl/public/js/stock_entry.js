// Stock Entry

frappe.ui.form.on('Stock Entry', {
    // before_save: function(frm) {
    //     frm.trigger('set_uom_conversion_factor_to_batch_qty');
    // },

    set_uom_conversion_factor_to_batch_qty: function(frm) {
        if (frm.doc.stock_entry_type == "Material Transfer") {
            $.each(frm.doc.items || [], function(idx, row) {
                if (row.batch_no){
                    frappe.call({
                        method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
                        args: {
                            item_code: row.item_code,
                            warehouse: row.s_warehouse,
                            batch_no: row.batch_no, 
                        },
                        callback: (r) => {
                            if(!r.message) {
                                return;
                            }
                            let qty = r.message;
    
                            if (qty) {
                                frappe.model.set_value(row.doctype, row.name, "qty", qty);
                            }
                        }
                    })
                }
            })
        }
    }
})

frappe.ui.form.on('Stock Entry Detail', {
    // batch_no: function(frm, cdt, cdn) {
    //     const row = locals[cdt][cdn];

    //     frm.events.set_uom_conversion_factor_to_batch_qty(frm);
    // }
    batch_no: async function(frm, cdt, cdn) {
        console.log("from batch")
        const row = locals[cdt][cdn];
        if (row.s_warehouse){
            await frappe.call({
                method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
                args: {
                    item_code: row.item_code,
                    warehouse: row.s_warehouse,
                    batch_no: row.batch_no, 
                },
                callback: (r) => {
                    if(!r.message) {
                        return;
                    }
                    let qty = r.message;

                    if (qty) {
                        frappe.model.set_value(row.doctype, row.name, "qty", qty);
                    }
                }
            })
        }
        

    },

    s_warehouse: async function(frm, cdt, cdn) {
        console.log("from s_Warehouse")
        const row = locals[cdt][cdn];
        if (row.batch_no){
            await frappe.call({
                method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
                args: {
                    item_code: row.item_code,
                    warehouse: row.s_warehouse,
                    batch_no: row.batch_no, 
                },
                callback: (r) => {
                    if(!r.message) {
                        return;
                    }
                    let qty = r.message;

                    if (qty) {
                        frappe.model.set_value(row.doctype, row.name, "qty", qty);
                    }
                }
            })
        }
        

    }

})
