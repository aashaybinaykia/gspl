
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def after_insert(doc, method):
    create_item_barcode(doc)

@frappe.whitelist()
def on_trash(doc, method):
    delete_item_barcode(doc)


def create_item_barcode(doc):

    item = frappe.get_doc("Item", doc.item)
    item.append('barcodes', {
        'barcode': doc.name
    })
    item.save()


def delete_item_barcode(doc):

    item_barcode = frappe.db.get(doctype="Item Barcode", filters={'parent': doc.item, 'barcode': doc.name})
    if item_barcode:
        item_barcode = frappe.get_doc("Item Barcode", item_barcode.name)
        item_barcode.delete()
