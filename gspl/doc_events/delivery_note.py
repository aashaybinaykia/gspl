
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def validate(doc, method):
    update_packing_list(doc)


def update_packing_list(doc):
    for packed_item in doc.packed_items:
        product_bundle_item = frappe.get_doc("Product Bundle Item", {'parent': packed_item.parent_item, 'item_code': packed_item.item_code})
        packed_item.batch_no = product_bundle_item.batch_no
