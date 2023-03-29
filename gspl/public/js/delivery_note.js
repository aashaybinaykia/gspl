// Delivery Note

erpnext.stock.DeliveryNoteController = erpnext.stock.DeliveryNoteController.extend({
    selling_price_list() {
        console.log('overrided');
    }
})

$.extend(cur_frm.cscript, new erpnext.stock.DeliveryNoteController({frm: cur_frm}));

frappe.ui.form.on('Delivery Note', {

    // validate: function(frm) {
    //     console.log("Validate Starts")
    //     $.each(frm.doc.items || [], function(idx, row) {
    //         console.log(row)
    //         if (row.batch_no){
    //             frappe.call({
    //                 method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
    //                 args: {
    //                     item_code: row.item_code,
    //                     warehouse: row.warehouse,
    //                     batch_no: row.batch_no, 
    //                 },
    //                 callback: (r) => {
    //                     console.log(r)
    //                     if(!r.message) {
    //                         return;
    //                     }
    //                     let qty = r.message;

    //                         if (qty) {
    //                             frappe.model.set_value(row.doctype, row.name, "qty", qty);
    //                         }
    //                     }
    //             })
    //         }
    //     })
    // },

    on_submit: function(frm){
        console.log(frm.doc.case_details)
    },
    sales_order: function(frm){
        console.log("From Sales Order")
        frm.set_value("ignore_pricing_rule",true)
    },
    customer: function(frm){
        frappe.call({
            method: 'frappe.client.get_value',
            args: {
                'doctype': 'Customer',
                'filters': {'name': frm.doc.customer},
                'fieldname': 'default_transporter'
            },
            callback: (r) => {
                if(r.message.default_transporter){
                    frm.set_value('transporter',r.message.default_transporter);
                    frm.script_manager.trigger('transporter')
                }
                else{
                    frm.set_value('transporter',"");
                    frm.refresh_field('transporter')

                }
            }
        })
        frm.set_query("sales_order", function() {
            return {
                "filters": {
                    "customer": frm.doc.customer,
                    "docstatus": 1
                }
            };
        });
    },
    

    scan_case: async function (frm) {
        console.log('From Scan Bundle')
        try {
            await frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Case Detail',
                    filters: {
                        name: frm.doc.scan_case
                    },
                    
                },
                callback: async function(data){
                    console.log(data)
                    if(!data.message){
                        frappe.show_alert({
                            message:__('Could not find the Bundle'),
                            indicator:'Red'
                        }, 3);
                        return
                    }
                    

                    var r = data.message
                    console.log(r)
                    var i
                    var j
                    var batches = []
                    if(frm.doc.case_details){
                        for(j =frm.doc.case_details.length-1;j>=0;j--){
                            if(frm.doc.case_details[j].case_detail==r.name)
                                frm.doc.scan_case = ""
                                frm.refresh_field('scan_case')
                                return
                        }
                    }
                    else j = 0
                    if( j == 0 || frm.doc.case_details.length == 0){
                        var bundle = frm.add_child('case_details', {
                            'case_detail' : r.name
                        })
                    }

                    frappe.run_serially([
                        async () => {
                            for(i=0;i<r.items.length;i++){
                                var item = r.items[i]
                                console.log(item)
                                let row = await frm.add_child('items', {
                                    item_code : item.item_code,
                                    qty: item.qty,
                                    batch_no: item.batch_no,
                                    uom: item.upm,
                                    price_list:frm.doc.selling_price_list,
                                    case_detail: r.name
                                });
                                console.log(row)
                                batches.push(item.batch_no)
                                frm.script_manager.trigger('item_code', row.doctype, row.name);
                                //frm.trigger(row.item_code)
                            }
                        },
                        () => {
                            
                            console.log(batches)
                            //batches = "[".concat(batches).concat("]")
                            batches = JSON.stringify(batches)
                            console.log(bundle)
                            if(bundle) bundle.batches = batches
                            frm.refresh_field('case_details')
                            console.log(bundle)
                            frm.refresh_field('items')
                            frm.doc.scan_case = ""
                            frm.refresh_field('scan_case')
                        }
                    ])
                }
            })
        }
        catch (r){
            return
        }
    },





})

frappe.ui.form.on('Case Entry Table Delivery Note', {
    before_case_details_remove(frm,cdt,cdn){
        const row = locals[cdt][cdn];
        console.log(row)
        var i
        for(i=0;i<frm.doc.items.length;i++){
            if(frm.doc.items[i].case_detail == row.case_detail){
                frm.doc.items.splice(i,1)
                i=i-1             
            }
            if(i>=0 && i<frm.doc.items.length) frm.doc.items[i].idx = i+1
        }
        frm.refresh_field('items')
    }
})

frappe.ui.form.on('Delivery Note Item', {
    setup: function(frm, cdt, cdn){
        console.log(frm)
        console.log(cdt)
        console.log(cdn)
    },
    items_add: function(frm, cdt, cdn){
        console.log(frm)
        console.log(cdt)
        console.log(cdn)
        const row = locals[cdt][cdn];
        frappe.model.set_value(row.doctype, row.name, "price_list", frm.doc.selling_price_list);
        console.log(frm.doc.items)

    },
    
    items_remove: function(frm, cdt, cdn){
        console.log(frm)
        console.log(cdt)
        console.log(cdn)

    },
    price_list: function(frm,cdt,cdn){
        const row = locals[cdt][cdn];
        frm.set_value('selling_price_list',row.price_list)
        frm.script_manager.trigger('item_code', cdt, cdn);
    },    
    batch_no: async function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];

        if (row.batch_no){
            await frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'Batch',
                    filters: {
                        'name': row.batch_no,
                    },
                    fieldname: ['batch_qty','disabled']
                },
                callback: function(r) {
                    if(!r.message) {
                        return;
                    }
                    if(r.message.disabled == 1){
                        if (row.case_detail == "" || row.case_detail == undefined){
                            frappe.msgprint({
                                title: __('Error'),
                                message:__('Row Removed Because Disabled Item Selected Without Case Detail'),
                                indicator:'red'
                            });
                            frm.doc.items.splice(row.idx-1,1)
                            frm.refresh_field('items')
                            return

                        }
                    }
                    let qty = r.message.batch_qty;
                    frappe.model.set_value(cdt, cdn, "qty", qty);
                }
            })
        }
    }
})
