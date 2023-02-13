
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint
from erpnext.stock.doctype.batch.batch import get_batch_qty
from frappe.utils import cint, flt

from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

from frappe.utils import logger

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

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
        if is_product_bundle(row.product_bundle):
            frappe.db.set_value("Product Bundle", row.item_code, "status", status)
