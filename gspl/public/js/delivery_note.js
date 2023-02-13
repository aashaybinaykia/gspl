// Delivery Note

frappe.ui.form.on('Delivery Note', {
    /*onload: function(frm){
        console.log(frm.doc)
        console.log(frm.doc.sales_order)
        console.log(frm.doc.__islocal)
        if(frm.doc.__islocal){
            console.log("Hi from for")
            var i
            for(i=0;i<frm.doc.items.length;i++){
                console.log(i)
                frm.doc.items[i].batch_no = ""
                console.log(frm.doc.items[i])
            }
            frm.refresh_field('items')
        }
        console.log(frm.doc)
    },*/
    onload: function(frm){
        //var addITem
    },
    
    validate: async function(frm) {
        console.log(frm)
        var i
        var row
            for(i=0;i<frm.doc.items.length;i++){
                row = frm.doc.items[i]
                if (row.batch_no !== undefined && row.batch_no !== ''){
                    console.log(row)
                    await frappe.call({
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
                                frappe.model.set_value(row.doctype, row.name, "qty", qty);
                            }
                        }
                    })
                }
                else {
                    await frappe.call({
                        method: 'frappe.client.get_value',
                        args: {
                            'doctype': 'Item',
                            'filters': {'name': row.item_code},
                            'fieldname': 'has_batch_no'
                        },
                        callback: (r) => {
                            console.log(r)
                            if(!r.message) {
                                return;
                            }
                            else {
                                if(r.message.has_batch_no == 1){
                                    var arr = frm.doc.items.splice(i,1)
                                    i=i-1
                                    frm.refresh_field('items')
                                }
                            }
                        }
                    })
                }
                if(i>=0 && i<frm.doc.items.length) frm.doc.items[i].idx = i+1
            }
        
    },  
    // before_save: function(frm) {
    //     $.each(frm.doc.items || [], function(idx, row) {
    //         if (row.batch_no){
    //             frappe.call({
    //                 method: 'erpnext.stock.doctype.batch.batch.get_batch_qty',
    //                 args: {
    //                     item_code: row.item_code,
    //                     warehouse: row.warehouse,
    //                     batch_no: row.batch_no, 
    //                 },
    //                 callback: (r) => {
    //                     if(!r.message) {
    //                         return;
    //                     }
    //                     let qty = r.message;

    //                     if (qty) {
    //                         frappe.model.set_value(row.doctype, row.name, "qty", qty);
    //                     }
    //                 }
    //             })
    //         }
    //     })
    // },
    selling_price_list: function(frm){
        return;
    },

    add_batch: async function(frm) {
        console.log(frm.doc)
        await frappe.call({
            method: 'frappe.client.get_value',
            args: {
                doctype: 'Batch',
                filters: {
                    'name': frm.doc.add_batch,
                },
                fieldname: ['name','batch_qty','item']
            },
            callback: function(data) {
                console.log(data)
                if(frm.doc.add_batch !== "")
                {    
                    if(!data.message.item){
                        frappe.show_alert({
                            message:__('Could not find the Batch'),
                            indicator:'Red'
                        }, 5);
                    }
                    else
                    {
                        console.log(data)
                        console.log(frm)
                        var item = frm.doc.items.find(element => element.item_code == data.message.item && (element.batch_no == "" || element.batch_no == undefined))
                        console.log(item)
                        var exists = frm.doc.items.find(element => element.batch_no == data.message.name)
                        if(exists) item = exists
                        if(item){
                            //frm.doc.addItem = item
                            item.batch_no = data.message.name
                            item.qty = data.message.batch_qty
                            if(frm.doc.add_bundle_batches !== undefined) item.product_bundle = frm.doc.add_bundle_batches //if called from add bundle batches
                            frm.refresh_field('items')
                        }
                        else{
                            var addItem = frm.doc.items.find(element => element.product_bundle == frm.doc.add_bundle_batches )
                            if(!addItem || frm.doc.items.find(element => element.batch_no == data.message.name)){//if an item from the bundle does not exist, incase it exists, it is not the same item as this batch else this batch will be entered twice. 
                                frappe.show_alert({
                                    message:__('Could Not Find Item For This Barcode'),
                                    indicator:'Red'
                                }, 5);
                            }
                            else {
                                var newChild = {...addItem}
                                newChild.name = undefined
                                newChild.idx = undefined
                                newChild.child_docname = undefined
                                newChild.incoming_rate = undefined
                                newChild.batch_no = data.message.name
                                newChild.item_code = data.message.item
                                newChild.qty = data.message.batch_qty
                                console.log("newchild")
                                console.log(newChild)
                                
                                let row = frm.add_child('items', newChild);
                                console.log(row)
                                frm.script_manager.trigger('item_code', row.doctype, row.name);
                                
                                frappe.show_alert({
                                    message:__('Added new Item from Bundle'),
                                    indicator:'Green'
                                }, 5);
                            }
                            frm.refresh_field('items')
                        }
                        frm.doc.add_batch = ""
                        frm.refresh_field('add_batch')
                        console.log(item)
                    }
                }
            }
        })
    },

    scan_bundle: async function (frm) {
        console.log('From Scan Bundle')
        try {
            await frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Product Bundle',
                    filters: {
                        name: frm.doc.scan_bundle
                    },
                    
                },
                callback: async function(data){
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
                    for(j =frm.doc.product_bundles.length-1;j>=0;j--){
                        if(frm.doc.product_bundles[j]==r.name)
                            break
                    }
                    if( j == 0 || frm.doc.product_bundles.length == 0){
                        var bundle = frm.add_child('product_bundles', {
                            'product_bundle' : r.name
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
                                    product_bundle: r.name
                                });
                                console.log(row)
                                batches.push(item.batch_no)
                                frm.script_manager.trigger('item_code', row.doctype, row.name);
                                //frm.trigger(row.item_code)
                            }
                        },
                        () => {
                            
                            console.log(batches)
                            batches = "[".concat(batches).concat("]")
                            console.log(bundle)
                            if(bundle) bundle.batches = batches
                            frm.refresh_field('product_bundles')
                            console.log(bundle)
                            frm.refresh_field('items')
                            frm.doc.scan_bundle = ""
                            frm.refresh_field('scan_bundle')
                        }
                    ])
                }
            })
        }
        catch (r){
            return
        }
    },




    add_bundle_batches: async function (frm) {
        console.log('From Scan Bundle')
        try {
            await frappe.call({
                method: 'frappe.client.get',
                args: {
                    doctype: 'Product Bundle',
                    filters: {
                        name: frm.doc.add_bundle_batches
                    },
                    
                },
                callback: async function(data){
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
                    console.log(frm.doc.items['product_bundles'])
                    for(j =frm.doc.product_bundles.length-1;j>=0;j--){
                        if(frm.doc.product_bundles[j]==frm.doc.add_bundle_batches)
                        break
                    }
                    if( j == 0 || frm.doc.product_bundles.length == 0){
                        var bundle = frm.add_child('product_bundles', {
                            'product_bundle' : frm.doc.add_bundle_batches
                        })
                    }
                    var batches = []
                    frappe.run_serially([
                        async () => {
                            
                            for(i=0;i<r.items.length;i++){
                                var item = r.items[i]
                                console.log(item)
                                var row = await frm.set_value('add_batch',item.batch_no)
                                batches.push(item.batch_no)
                                console.log(row)
                            }
                        },
                        () => {
                            //console.log(frm.doc.addItem)
                            console.log(batches)
                            batches = "[".concat(batches).concat("]")
                            console.log(bundle)
                            if(bundle) bundle.batches = batches
                            frm.refresh_field('product_bundles')
                            console.log(bundle)
                            frm.doc.add_bundle_batches = ""
                            frm.refresh_field('add_bundle_batches')
                        }
                    ])
                }
            })
        }
        catch (r){
            return
        }
    }



})

frappe.ui.form.on('Bundle Entry Table', {
    before_product_bundles_remove(frm,cdt,cdn){
        const row = locals[cdt][cdn];
        console.log(row)
        var i
        for(i=0;i<frm.doc.items.length;i++){
            if(frm.doc.items[i].product_bundle == row.product_bundle){
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
                    frappe.model.set_value(cdt, cdn, "qty", qty);

                    /*if (qty) {
                        setTimeout(() => {
                            frappe.model.set_value(cdt, cdn, "qty", qty);
                        }, 2000);
                    }*/
                }
            })
        }
    }
})
