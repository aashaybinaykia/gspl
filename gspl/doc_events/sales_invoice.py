
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def on_submit(doc, method):
    if not doc.is_return:
        update_product_bundle(doc, "Sold")
    else:
        update_product_bundle(doc, "Active")

@frappe.whitelist()
def on_cancel(doc, method):
    if not doc.is_return:
        update_product_bundle(doc, "Active")
    else:
        update_product_bundle(doc, "Sold")


def update_product_bundle(doc, status):
    from erpnext.stock.doctype.packed_item.packed_item import is_product_bundle

    for row in doc.items:
        if is_product_bundle(row.item_code):
            frappe.db.set_value("Product Bundle", row.item_code, "status", status)
