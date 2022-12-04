
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def validate(doc, method):
    update_packing_list(doc)

@frappe.whitelist()
def before_save(doc, method):
    set_uom_conversion_factor_to_batch_qty(doc)


def update_packing_list(doc):
    for packed_item in doc.packed_items:
        product_bundle_item = frappe.get_doc("Product Bundle Item", {'parent': packed_item.parent_item, 'item_code': packed_item.item_code})
        packed_item.batch_no = product_bundle_item.batch_no


def set_uom_conversion_factor_to_batch_qty(doc):
    for row in doc.items:
        if row.batch_no:
            batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=row.warehouse, item_code=row.item_code)

            if batch_qty:
                row.conversion_factor = batch_qty
