
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def before_save(doc, method):
    calculate_rate_and_qty(doc)
    enable_disable_batch(doc)

def calculate_rate_and_qty(doc):
    total_rate = sum([row.rate for row in doc.items])
    total_qty = sum([row.qty for row in doc.items])

    doc.total_rate = total_rate
    doc.total_qty = total_qty


def enable_disable_batch(doc):
    if doc.enabled:
        for row in doc.items:
            batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=doc.warehouse, item_code=row.item_code)

            if batch_qty < row.qty:
                frappe.throw(_(
                    "Row #%s: Cannot enable Product Bundle because Batch %s does not have enough stock." % (
                        row.idx, row.batch_no,)))

            else:
                frappe.db.set_value("Batch", row.batch_no, 'disabled', True)

        frappe.db.set_value("Item", doc.new_item_code, 'is_sales_item', True)
        doc.status = "Active"

    else:
        for row in doc.items:
            frappe.db.set_value("Batch", row.batch_no, 'disabled', False)
        
        frappe.db.set_value("Item", doc.new_item_code, 'is_sales_item', False)
        doc.status = "Disabled"
