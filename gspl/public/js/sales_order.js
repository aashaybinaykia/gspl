// Sales Order

// cur_frm.cscript.so_type = function(doc, cdt, cdn) {
// 	let so_type = doc.so_type;
// 	console.log(so_type);

// 	if(so_type == "Loose Item") {
// 		cur_frm.set_query("item_code", "items", function() {
// 			return {
// 				query: "erpnext.controllers.queries.item_query",
// 				filters: {'is_sales_item': 1, 'customer': cur_frm.doc.customer, 'has_variants': 0}
// 			}
// 		});
// 	// } else if (so_type == "Single Sort") {
// 	} else {
// 		cur_frm.set_query("item_code", "items", function() {
// 			return {
// 				query: "erpnext.controllers.queries.item_query",
// 				filters: {'is_sales_item': 1, 'customer': cur_frm.doc.customer, 'has_variants': 1}
// 			}
// 		});
// 	}
// }

frappe.ui.form.on('Sales Order', {
    validate: function(frm) {
        frm.clear_table('items');
        $.each(frm.doc.order_entry_items, function(i, row) {
            frm.events.update_items_table_based_on_order_entry_item(frm, row);
        });
    },

    calculate_final_rate: function(frm) {
        $.each(frm.doc.order_entry_items, function(idx, row) {
            let final_rate = flt(row.price_list_rate) - flt(row.discount_amount);
            frappe.model.set_value(row.doctype, row.name, "final_rate", final_rate);
        })
    },

    update_items_table_based_on_order_entry_item: function(frm, order_entry_item) {
        frappe.call({
            method: "gspl.doc_events.sales_order.get_so_items",
            args: {
                doc: frm.doc,
                order_entry_item: order_entry_item,
            },
            callback: function(r) {
                if(r.message) {
                    let response = r.message;
                    let data = response.data;

                    $.each(data || [], function(i, d) {
                        if (!frm.doc.items.filter((d) => order_entry_item.item_code == d.item_code).length) {
                            let child = frm.add_child('items', d);
                            frm.script_manager.trigger('item_code', child.doctype, child.name);
                        }
                    })

                    frm.refresh_field('items');
                }
            }
        })
    }
})

frappe.ui.form.on('Sales Order Item', {
    stock_uom_rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        let rate = flt(row.stock_uom_rate) * flt(row.conversion_factor);

        frappe.model.set_value(cdt, cdn, "rate", rate);
    }
})


frappe.ui.form.on('Sales Order Entry Item', {
    order_entry_items_add: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(row.doctype, row.name, "price_list", frm.doc.selling_price_list);
    },

    item_code: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frm.events.update_items_table_based_on_order_entry_item(frm, row);
    },

    qty: function(frm, cdt, cdn) {
        frm.events.calculate_final_rate(frm);
    },

    price_list_rate: function(frm, cdt, cdn) {
        frm.events.calculate_final_rate(frm);
    },

    discount_percentage: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        let discount_amount = 0;

        discount_amount = flt(row.price_list_rate) * flt(row.discount_percentage) / 100.0;

        frappe.model.set_value(cdt, cdn, "discount_amount", discount_amount);
        // frm.events.calculate_final_rate(frm);
    },

    discount_amount: function(frm, cdt, cdn) {
        frm.events.calculate_final_rate(frm);
    },
})
