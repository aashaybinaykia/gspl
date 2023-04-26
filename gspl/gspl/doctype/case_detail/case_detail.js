// Copyright (c) 2023, GSPL and contributors
// For license information, please see license.txt

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


frappe.ui.form.on('Case Detail', {
    before_save: function(frm) {
        frm.trigger('calculate_rate_and_qty')
    },

    calculate_qty_and_amt: function(frm) {
        // Calculates 'Total Qty' and 'Total Amount'
        let total_qty = frappe.utils.sum((frm.doc.items || []).map((d) => {return flt(d.qty)}));
        let total_amount = frappe.utils.sum((frm.doc.items || []).map((d) => {return flt(d.rate) * flt(d.qty)}));

        frm.set_value('total_qty', flt(total_qty))
        frm.set_value('total_amount', flt(total_amount))
    },

	scan_barcode: function(frm) {
		const barcode_scanner = new erpnext.utils.BarcodeScanner({frm: frm});
		barcode_scanner.process_scan();
	}
})


frappe.ui.form.on('Case Detail Item', {
    qty: function(frm, cdt, cdn) {
        frm.events.calculate_qty_and_amt(frm)
    },

    rate: function(frm, cdt, cdn) {
        frm.events.calculate_qty_and_amt(frm)
    },
    
    items_remove: function(frm, cdt, cdn){
        console.log(frm)
        console.log(cdt)
        console.log(cdn)

    },
    batch_no: async function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (row.batch_no){
            await frappe.call({
                method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
                args: {
                    item_code: row.item_code,
                    warehouse: frm.doc.warehouse,
                    batch_no: row.batch_no, 
                },
                callback: (r) => {
                    if(!r.message) {
                        return;
                    }
                    console.log(r)
                    let qty = r.message;
                    console.log(qty)
                    frappe.model.set_value(cdt, cdn, "qty", qty);
                    
                }
            })

            await frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Stock Ledger Entry',
                    filters: {
                        'item_code': frm.doc.item_consumed,
                        'is_cancelled': 0
                    },
                    fieldname: ['valuation_rate']
                },
                callback: function(data) {
                    //console.log(data.message);
                    frappe.model.set_value(cdt, cdn, "rate", data.message.valuation_rate);
                }
    
            });
        }
    }
})
