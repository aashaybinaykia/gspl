
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint
from erpnext.stock.doctype.batch.batch import get_batch_qty
from frappe.utils import cint, flt

from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

from frappe.utils import logger
import json

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

@frappe.whitelist()
def on_submit(doc, method):
    if not doc.is_return:
        update_case_detail(doc, "Sold")
    else:
        update_case_detail(doc, "Active")

@frappe.whitelist()
def on_cancel(doc, method):
    if not doc.is_return:
        update_case_detail(doc, "Active")
    else:
        update_case_detail(doc, "Sold")

@frappe.whitelist()
def validate(doc, method):

    #Get all batches from item table - master_batches
    master_batches = set()
    for row in doc.items:
        master_batches.add(str(row.batch_no))
    
    #Iterate through all product bundles, convert 'batches' json to array - 'product_batches'
    #Inside iteration, check if 'product_batches' is a subset of 'master_batches'
    for row in doc.case_details:
        bundle_batches_json_string = row.batches
        bundle_batches = json.loads(bundle_batches_json_string)
        missing_batches = set()

        for b in bundle_batches:
            if b not in master_batches:
                missing_batches.add(b)

        if len(missing_batches) != 0:
            frappe.throw(_("Batches "+str(missing_batches)+" From Bundle "+str(row.case_detail)+" Not Present in Items Table"))

    
    sales_order_item_table = frappe.get_doc('Sales Order', doc.sales_order).items
    if sales_order_item_table:
        for row in doc.items:
            if not row.so_detail:
                for so_row in sales_order_item_table:
                    if so_row.delivered_qty > 0:
                        sales_order_item_table.remove(so_row)
                        continue

                    if so_row.item_code == row.item_code: # Check if this row's item code is same as row.itemcode
                        row.so_detail = so_row.name
                        row.against_sales_order = doc.sales_order
                        row.price_list = so_row.price_list
                        row.price_list_rate = so_row.price_list_rate
                        row.base_price_list_rate = so_row.base_price_list_rate
                        row.discount_percentage = so_row.discount_percentage
                        row.discount_amount = so_row.discount_amount
                        row.rate = so_row.rate

                        logger.info("Assigning so_detail to item code "+row.item_code+" in Delivery Note")
                        logger.info(row)
                        sales_order_item_table.remove(so_row)
                        break
            
            if not row.so_detail:
                logger.debug("Item code "+row.item_code+" was not assigned any so_detail value")
    else:
        logger.debug("Could not find Sales Order "+doc.sales_order)


def update_case_detail(doc, status):

    for row in doc.case_details:
        if (row.case_detail):
            frappe.db.set_value("Case Detail", row.case_detail, "status", status)
