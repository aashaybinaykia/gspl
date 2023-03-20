
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt


@frappe.whitelist()
def after_insert(doc, method):
    #: No need to add batch in items barcode field since scan_barcode also scans for batch_no automatically
    # create_item_barcode(doc)
    set_highest_item_batch_qty(doc)


def set_highest_item_batch_qty(doc):
    item = frappe.get_doc("Item", doc.item)

    if (flt(doc.batch_qty) <21) & (flt(doc.batch_qty) > flt(item.batch_qty)):
        item.batch_qty = flt(doc.batch_qty)
        item.save()

# @frappe.whitelist()
# def on_trash(doc, method):
#     delete_item_barcode(doc)


#: No need to add batch in items barcode field since scan_barcode also scans for batch_no automatically
# def create_item_barcode(doc):
#     item = frappe.get_doc("Item", doc.item)
#     item.append('barcodes', {
#         'barcode': doc.name
#     })
#     item.save()


# def delete_item_barcode(doc):

#     item_barcode = frappe.db.get(doctype="Item Barcode", filters={'parent': doc.item, 'barcode': doc.name})
#     if item_barcode:
#         item_barcode = frappe.get_doc("Item Barcode", item_barcode.name)
#         item_barcode.delete()
