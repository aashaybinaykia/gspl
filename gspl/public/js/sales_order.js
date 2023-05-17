

erpnext.selling.CustomSalesOrderController = class CustomSalesOrderController extends erpnext.selling.SalesOrderController {
    selling_price_list() {
        console.log('overrided');
    }
}

extend_cscript(cur_frm.cscript, new erpnext.selling.CustomSalesOrderController({frm: cur_frm}));

frappe.ui.form.on('Sales Order', {
    onload_post_render: function(frm) {
        frm.get_field("order_entry_items").grid.set_multiple_add("order_item", "qty");
    },

    calculate_final_rate: function(row) {
        if(row.discount_percentage > 0){
            let discount_amount = 0;
            discount_amount = flt(row.price_list_rate) * flt(row.discount_percentage) / 100.0;
    
            if(row.discount_amount != discount_amount) {
                row.discount_amount = discount_amount;
            }
        }
        let final_rate = flt(row.price_list_rate) - flt(row.discount_amount);
        frappe.model.set_value(row.doctype, row.name, "final_rate", final_rate);        
    },
})

frappe.ui.form.on('Sales Order Item', {
    stock_uom_rate(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        let rate = flt(row.stock_uom_rate) * flt(row.conversion_factor);

        frappe.model.set_value(cdt, cdn, "rate", rate);
    },
    order_items_add: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(row.doctype, row.name, "price_list", frm.doc.selling_price_list);
    },
    price_list: function(frm,cdt,cdn){
        const row = locals[cdt][cdn];
        frm.set_value('selling_price_list',row.price_list)
        frm.script_manager.trigger('item_code', cdt, cdn);
    },    
})


frappe.ui.form.on('Sales Order Entry Item', {
    order_entry_items_add: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        frappe.model.set_value(row.doctype, row.name, "price_list", frm.doc.selling_price_list);
    },

    order_item: async function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
		var me = frm;
		var item = frappe.get_doc(cdt, cdn);
        var item_name;
        console.log(item)

        if(row.order_item && row.order_item != ""){
            frappe.call({
                method: "gspl.doc_events.sales_order.populate_order_item",
                args: {
                    item_code: row.order_item,
                    company: frm.doc.company,
                    customer: frm.doc.customer,
                    currency: frm.doc.currency,
                    price_list: row.price_list,
                    date: frm.doc.transaction_date,
                    project: frm.doc.project || "",
                    cdn: cdn,
                    name: frm.doc.name
                },

                callback: function(r){
                    console.log(r)
                    if(r.message) {
                        console.log(r.message)
                        row.price_list_rate = r.message.price_list_rate,
                        row.discount_amount = r.message.discount_amount,
                        row.discount_percentage = r.message.discount_percentage
                        row.final_rate = r.message.final_rate
                        row.items = r.message.items
                        row.brand = r.message.brand
                        console.log(row)
                        frm.refresh_field('order_entry_items')
                    }
                }
            })
        }		
	},

    price_list: function(frm,cdt,cdn){
        frm.script_manager.trigger('order_item', cdt, cdn);
    },
    price_list_rate: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        console.log(row)
        frm.events.calculate_final_rate(row);
    },

    discount_percentage: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        console.log(row)
        console.log("From Discount")
        let discount_amount = 0;

        discount_amount = flt(row.price_list_rate) * flt(row.discount_percentage) / 100.0;

        if(row.discount_amount != discount_amount) {
            frappe.model.set_value(cdt, cdn, "discount_amount", discount_amount);
        }
    },

    discount_amount: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        console.log(row)
        let discount_percentage = 0;
        discount_percentage = flt(row.discount_amount) * 100 / (row.price_list_rate);
        if(row.discount_percentage != discount_percentage){
            frappe.model.set_value(cdt, cdn, "discount_percentage", discount_percentage);      
        }
        frm.events.calculate_final_rate(row);
    },
})
