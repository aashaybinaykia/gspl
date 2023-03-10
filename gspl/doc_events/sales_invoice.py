
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def validate(doc, method):
    if not doc.is_return:
        update_uom_conversion_factor_in_sales_order(doc)

@frappe.whitelist()
def before_save(doc, method):
    set_uom_conversion_factor_to_batch_qty(doc)



def update_uom_conversion_factor_in_sales_order(doc):
    for row in doc.items:
        if row.so_detail:
            # so = frappe.get_doc("Sales Order", row.sales_order)
            frappe.db.set_value("Sales Order Item", row.so_detail, 'conversion_factor', row.conversion_factor)
            # TODO: Calculate Rate and Stock UOM Rate (Need to check what else needs to be calculated here)
            # stock_uom_rate = frappe.db.get_value("Sales Order Item", row.so_detail, 'stock_uom_rate')
            # rate = stock_uom_rate * row.conversion_factor
            # frappe.db.set_value("Sales Order Item", row.so_detail, 'rate', rate)

            # so.submit()

def set_uom_conversion_factor_to_batch_qty(doc):
    for row in doc.items:
        if row.batch_no:
            batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=row.warehouse, item_code=row.item_code)

            if batch_qty:
                row.conversion_factor = batch_qty



