
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def validate(doc, method):
    validate_batch_qty(doc)


def validate_batch_qty(doc):

    # Return if Voucher Type is "Stock Entry" and Stock Entry Type is "Repack"
    if doc.voucher_type == "Stock Entry":
        stock_entry_type = frappe.db.get_value(doc.voucher_type, doc.voucher_no, 'stock_entry_type')

        if stock_entry_type == "Repack":
            return

    batch_qty = get_batch_qty(batch_no=doc.batch_no, warehouse=doc.warehouse, item_code=doc.item_code)

    if doc.actual_qty < batch_qty:
        frappe.throw(
            _("Cannot transfer partial quantity for Batch {}.").format(doc.batch_no))