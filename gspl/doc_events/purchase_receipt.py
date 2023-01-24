
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def validate(doc, method):
    validate_if_product_bundle_exists(doc)

@frappe.whitelist()
def on_submit(doc, method):
    create_product_bundles(doc)

@frappe.whitelist()
def before_cancel(doc, method):
    delete_product_bundles(doc)


def validate_if_product_bundle_exists(doc):    
    for row in doc.items:
        if row.product_bundle_id:
            if frappe.db.exists("Product Bundle", row.product_bundle_id):
                frappe.throw(_(
                    "Row #%s: Product Bundle %s already exists for item %s. " 
                    "Please use different Product Bundle ID" % (
                        row.idx, row.product_bundle_id, row.item_name,)))


def create_product_bundles(doc):
    product_bundles = {}
    for row in doc.items:
        if row.product_bundle_id and row.batch_no:
            key = (row.product_bundle_id, row.item_group, row.warehouse)
            product_bundles.setdefault(key, [])
            product_bundles[key].append(row)


    for (product_bundle_id, item_group, warehouse), items in product_bundles.items():
        item = frappe.get_doc(dict(
                doctype = "Item",
                item_code = product_bundle_id,
                item_name = product_bundle_id,
                item_group = item_group,
                is_stock_item = False,
                has_batch_no = False,
                stock_uom = "Nos",
                # is_sales_item = True,
            )).insert()

        bundle = frappe.new_doc("Product Bundle")
        bundle.new_item_code = item.name
        bundle.warehouse = warehouse

        for row in items:
            # Mark Batch as disabled
            frappe.db.set_value("Batch", row.batch_no, 'disabled', True)

            bundle.append('items', {
                'item_code': row.item_code,
                'qty': row.qty,
                'description': row.description,
                'rate': row.rate,
                'uom': row.uom,
                'batch_no': row.batch_no
            })

        bundle.save()


def delete_product_bundles(doc):
    product_bundles = list(set([row.product_bundle_id for row in doc.items if row.product_bundle_id and row.batch_no]))
    for bundle_item in product_bundles:
        bundle = frappe.get_doc("Product Bundle", bundle_item)
        bundle.delete()
        item = frappe.get_doc("Item", bundle_item)
        item.delete()
