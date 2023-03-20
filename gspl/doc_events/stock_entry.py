
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def before_save(doc, method):
    set_items_qty_to_batch_qty(doc)

@frappe.whitelist()
def before_submit(doc, method):
    if not doc.case_detail_transfer:
        validate_disabled_batch(doc)


@frappe.whitelist()
def before_cancel(doc, method):
    if not doc.case_detail_transfer:
        validate_disabled_batch_before_cancel(doc)


def set_items_qty_to_batch_qty(doc):
    for row in doc.items:
        if row.batch_no:
            batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=row.s_warehouse, item_code=row.item_code)

            if batch_qty:
                row.qty = batch_qty


def validate_disabled_batch(doc):
    for row in doc.items:
        if row.batch_no:
            disabled = frappe.db.get_value('Batch', row.batch_no, 'disabled')
            if disabled:
                frappe.throw(
                    _("Row #{0}: The batch {1} is disabled. Please select another batch which is enabled.").format(row.idx, row.batch_no))

def validate_disabled_batch_before_cancel(doc):
    for row in doc.items:
        if row.batch_no:
            disabled = frappe.db.get_value('Batch', row.batch_no, 'disabled')
            if disabled:
                frappe.throw(
                    _("Row #{0}: Cannot cancel document because the batch {1} is disabled.").format(row.idx, row.batch_no))
