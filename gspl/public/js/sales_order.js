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

erpnext.selling.CustomSalesOrderController = erpnext.selling.SalesOrderController.extend({
    selling_price_list() {
        console.log('overrided');
    }
})

$.extend(cur_frm.cscript, new erpnext.selling.CustomSalesOrderController({frm: cur_frm}));

frappe.ui.form.on('Sales Order', {
    timeline_refresh: function(frm){
        frm.doc.ignore_pricing_rule = false
    },
    validate: function(frm) {
        console.log("Validate Starts")
        frm.clear_table('items');
        var i
        var row
        frm.doc.ignore_pricing_rule = true
        for(i=0;i<frm.doc.order_entry_items.length;i++){
            //frm.events.get_so_items(frm,row);
            row = frm.doc.order_entry_items[i]
            console.log(row)
            var j
            loop:
            for(j=0;j<row.qty;j++) {
                console.log(j)
                var itemDetails = JSON.parse(row.items)
                console.log(itemDetails)
                var k = 0
                var length = itemDetails.length
                if(length == undefined || length == null || length <= 0) length = 1
                console.log(length)
                var details
                for(k = 0;k<length;k++){
                    if(!itemDetails.length) details = itemDetails; else details = itemDetails[k]
                    console.log(details)
                    console.log(k)
                    if(details.has_batch_no ==1 && details.batch_qty >0) {
                        frm.events.add_child_to_so(frm,row,details.batch_qty,details)
                        
                    }
                    
                    else if(details.has_batch_no == 0){
                        frm.events.add_child_to_so(frm,row,row.qty,details)
                        break loop
                    }
                }
            }
        };


        frm.set_value('shipping_address_name', frm.doc.customer_address);
    },

    calculate_final_rate: function(row) {
            console.log(row)
            let discount_amount = 0;
    
            discount_amount = flt(row.price_list_rate) * flt(row.discount_percentage) / 100.0;
    
            if(row.discount_amount != discount_amount) {
                row.discount_amount = discount_amount
            }
            let final_rate = flt(row.price_list_rate) - flt(row.discount_amount);
            frappe.model.set_value(row.doctype, row.name, "final_rate", final_rate);
    },
    update_prices: function(me,row,item,item_code) {
        if(item_code) {
            {
                item.pricing_rules = ''
                return frappe.call({
                    method: "erpnext.stock.get_item_details.get_item_details",
                    child: item,
                    args: {
                        args: {
                            item_code: item_code,
                            set_warehouse: me.doc.set_warehouse,
                            customer: me.doc.customer,
                            currency: me.doc.currency,
                            update_stock: 0,
                            conversion_rate: me.doc.conversion_rate,
                            price_list: row.price_list,
                            price_list_currency: me.doc.price_list_currency,
                            plc_conversion_rate: me.doc.plc_conversion_rate,
                            company: me.doc.company,
                            order_type: me.doc.order_type,
                            ignore_pricing_rule: me.doc.ignore_pricing_rule,
                            doctype: me.doc.doctype,
                            name: me.doc.name,
                            project: item.project || me.docproject,
                            qty: item.qty || 1,
                            net_rate: item.rate,
                            stock_qty: item.stock_qty,
                            tax_category: me.doc.tax_category,
                            child_docname: item.name,
                        }
                    },

                    callback: function(r) {
                        console.log(r)
                        if(!r.exc) {
                            
                            frappe.run_serially([
                                () => {
                                    frappe.model.set_value(row.doctype, row.name, "price_list_rate", r.message.price_list_rate);
                                    
                                },
                                () => {
                                    if(r.message.discount_percentage > 0){
                                        frappe.model.set_value(row.doctype, row.name, "discount_percentage", r.message.discount_percentage);
                                    }
                                    else {
                                        frappe.model.set_value(row.doctype, row.name, "discount_amount", r.message.discount_amount);
                                    }
                                }
                            ]);
                        }
                    }
                });
            }
        }
    },
    
    get_so_items: function(frm,row){
        console.log("Get SO Items");
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Item',
                    filters: {
                        'name': row.order_item,
                    },
                    fieldname: ['has_variants']
                },
                callback: function(data) {
                    var items = []
                    if(data.message.has_variants == 0){
                            items.push(row)
                        frm.events.fill_so_items(frm,items)
                    }
                    else {
                        frappe.call({
                            method: 'frappe.client.get_list',
                            args: {
                                doctype: 'Item',
                                filters: {
                                    'variant_of': row.order_item,
                                    'name': ['like', '%S%']
                                }
                            },
                            callback: function(data2){
                                var i
                                    for( i = 0;i<data2.message.length;i++){
                                        var temp = {
                                                    discount_amount: row.discount_amount,
                                                    discount_percentage: row.discount_percentage,
                                                    order_item: data2.message[i].name,
                                                    final_rate: row.final_rate,
                                                    // price_list: row.price_list,
                                                    price_list_rate: row.price_list_rate,
                                                    qty:row.qty
                                    }
                                    items.push(temp)
                                    }
                                frm.events.fill_so_items(frm,items)
                            }
                        })
                    }
                }
            })
    },
    
    fill_so_items: async function (frm,items){
        console.log("Fill SO Items")
        var i
        for(i = 0;i<items.length;i++){
            await frappe.call({
                method: 'frappe.client.get_list',
                args: {
                    doctype: 'Batch',
                    filters: {
                        'item': items[i].order_item
                    },
                    fields:['batch_qty'],
                    order_by: 'batch_qty desc',
                    pluck: 'batch_qty'
                },
                callback: function(data){
                   if(data.message[0] == undefined){
                        frm.events.add_child_to_so(frm,items[i],items[i].qty)
                   }
                   else {
                       var j
                       for (j=0;j<items[i].qty;j++){
                           frm.events.add_child_to_so(frm,items[i],data.message[0].batch_qty)
                       }
                   }
                }
                            
            })
        }
    },
    
    add_child_to_so: async function (frm,item,qty,details){
        console.log("Add Child To So")
        /*frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Item',
                filters: {
                    'name': item.order_item,
                },
                fieldname: ['item_name','description','stock_uom','gst_hsn_code']
            },
            callback: function(data) {
                details = data.message
                */
                let child = await frm.add_child('items',{
                    //item_code: item.order_item,
                    item_code:details.item_code,
                    qty: qty,
                    discount_amount: item.discount_amount,
                    discount_percentage: item.discount_percentage,
                    rate: item.final_rate,
                    price_list: frm.doc.selling_price_list,
                    price_list_rate: item.price_list_rate,
                    delivery_date: frm.doc.delivery_date,
                    item_name: details.item_name,
                    description: details.description,
                    uom: details.stock_uom,
                    get_hsn_code: details.get_hsn_code
                })
                console.log(child)
                frm.refresh_field('items')
            /*}
        })*/
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
        await frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Item',
                filters: {
                    'name': item.order_item,
                },
                fieldname: ['item_code','has_variants','has_batch_no','batch_qty','item_name','description','stock_uom','gst_hsn_code']
            },
            callback: async function(data) {
                if(data.message.has_variants == 0){
                    frm.events.update_prices(me,row,item,item.order_item)
                    console.log(data.message)
                    row.items = JSON.stringify(data.message)
                }
                else {
                    await frappe.call({
                        method: 'frappe.client.get_list',
                        args: {
                            doctype: 'Item',
                            fields: ['item_code','batch_qty','has_batch_no','item_name','description','stock_uom','gst_hsn_code'],
                            filters: {
                                'variant_of': item.order_item,
                                'name': ['like', '%S%']
                            }
                        },
                        callback: function(data2){
                            console.log(data2)
                            if(data2.message[0]){
                                item_name = data2.message[0].item_code
                                frm.events.update_prices(me,row,item,item_name)
                                row.items = JSON.stringify(data2.message)
                                console.log(row)
                                
                            }
                            else {
                                row.order_item = null
                                frappe.throw("No SL Items in this Sort")
                            }
                        }
                    })
                }

                
            }

        });


		
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
