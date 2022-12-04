
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def before_save(doc, method):
    set_bundle_type(doc)
    calculate_rate_and_qty(doc)
    enable_disable_batch(doc)


def set_bundle_type(doc):
    item_templates = []
    has_template = False
    template_name = "mixed"

    for row in doc.items:
        item = frappe.get_doc("Item", row.item_code)

        if item.variant_of:
            if item.variant_of not in item_templates:
                item_templates.append(item.variant_of)
                has_template = True
        else:
            has_template = False
            break


    if has_template and len(item_templates) == 1:
        template_name = item_templates[0]

    doc.bundle_type = template_name

    # Updates "Product Bundle Item Template" table
    doc.set('items_template', [])

    for item_template in item_templates:
        doc.append('item_templates', {
            'item_template': item_template,
        })


def calculate_rate_and_qty(doc):
    total_qty = sum([row.qty for row in doc.items])
    total_amount = sum([row.qty * row.rate for row in doc.items])

    doc.total_qty = total_qty
    doc.total_amount = total_amount


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
