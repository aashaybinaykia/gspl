
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import flt

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def validate(doc, method):
    if doc.batch_no:
        validate_batch_qty(doc)

@frappe.whitelist()
def on_submit(doc, method):
    if doc.batch_no:
        set_highest_item_batch_qty(doc)
        


def validate_batch_qty(doc):

    # Return if Voucher Type is "Stock Entry" and Stock Entry Type is "Repack"
    if doc.voucher_type == "Stock Entry":
        stock_entry_type = frappe.db.get_value(doc.voucher_type, doc.voucher_no, 'stock_entry_type')

        if stock_entry_type == "Repack" or stock_entry_type == "Material Receipt":
            return

    batch_qty = get_batch_qty(batch_no=doc.batch_no, warehouse=doc.warehouse, item_code=doc.item_code)

    if flt(batch_qty):
        if flt(abs(doc.actual_qty)) != flt(batch_qty):
            frappe.throw(
                _("Cannot transfer partial quantity {} for Batch {} (Batch qty: {}).").format(doc.actual_qty, doc.batch_no, batch_qty))


def set_highest_item_batch_qty(doc):
    if doc.item_code:
        item = frappe.get_doc("Item", doc.item_code)
        if (flt(doc.actual_qty) <21) & (flt(doc.actual_qty) > flt(item.batch_qty)):
            item.batch_qty = flt(doc.actual_qty)
            item.save()