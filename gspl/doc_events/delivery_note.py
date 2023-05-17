
from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.model.naming import parse_naming_series

from erpnext.stock.doctype.batch.batch import get_batch_qty

from frappe.utils import logger

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)


@frappe.whitelist()
def before_naming(doc, method):
    if doc.is_return == True:
        doc.naming_series = "DRET-.FY.-"


@frappe.whitelist()
def before_save(doc, method):
    series = parse_naming_series(doc.naming_series)
    doc.series_number = doc.name.removeprefix(series)


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

    ### Section 1: This section ensures that any item (if part of a case) is not accidentally deleted from the items table. 
                    # Essentially, all batch_no of a case present in the case_Detail table should be present in the items tables
    
    ### Section 2: This section sets the batch qty of each row
    ### Section 3: This section links the delivery note item to its corresponding sales order item and populates certain fields accordingly
    ### Section 3b: If extra items (not in sales order) from a case are present, populate fields according to other items from the same case.
    master_batches = set()

    case_dict = {}
    case_detail_rows_pending = False

    sales_order_item_table = []
    sales_order_exists = False
    if (doc.sales_order and doc.sales_order != ""):
        sales_order_item_table = frappe.get_doc('Sales Order', doc.sales_order).items
        sales_order_exists = True
    else:
        logger.debug("Could not find Sales Order")

    # Iterate through all rows in delivery note
    # And while looping through all items, 
    # 1. Get all batches from item table - master_batches
    # 2. Set batch qty
    # 3. If sales order is found, set so_detail value for these items (so_detail is the sales order item corresponding to the delivery note item)
    # 4. once so_detail is set, if case number is present in the row, add it to a hashmap for later use

    for row in doc.items:  

        # Part 1
        master_batches.add(str(row.batch_no)) 

        # Part 2
        batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=row.warehouse, item_code=row.item_code)
        if batch_qty>0 :
            row.qty = batch_qty
            row.stock_qty = row.qty * row.conversion_factor             
        
        # Part 3
        if sales_order_exists:
            if not row.so_detail:
                for so_row in sales_order_item_table:
                    if so_row.delivered_qty > 0:
                        sales_order_item_table.remove(so_row)
                        continue

                    if so_row.item_code == row.item_code: # Check if this row's item code is same as row.itemcode
                        row.so_detail = so_row.name
                        row.against_sales_order = doc.sales_order
                        row.price_list_rate = so_row.price_list_rate
                        row.base_price_list_rate = so_row.base_price_list_rate
                        row.discount_percentage = so_row.discount_percentage
                        row.discount_amount = so_row.discount_amount
                        row.rate = so_row.rate
                        row.price_list = so_row.price_list

                        logger.info("Assigning so_detail to item code "+row.item_code+" in Delivery Note")
                        logger.info(row)
                        sales_order_item_table.remove(so_row)

                        # Part 4
                        cd = row.case_detail
                        if cd and (case_dict.get(cd) == None):
                            logger.info('ENTERING DATA INTO DICT')
                            value_dict = {}
                            value_dict['price_list_rate'] = row.price_list_rate
                            value_dict['base_price_list_rate'] = row.base_price_list_rate
                            value_dict['discount_percentage'] = row.discount_percentage
                            value_dict['discount_amount'] = row.discount_amount
                            value_dict['rate'] = row.rate
                            value_dict['price_list'] = row.price_list
                                
                            case_dict[cd] = value_dict

                        break
            
            if not row.so_detail:
                logger.debug("Item code "+row.item_code+" was not assigned any so_detail value")
                if row.case_detail:
                    case_detail_rows_pending = True

    # Section 3b:
    # Iterate through all rows of delivery_note again if there are any case_detail rows left to fill details of
    if sales_order_exists and case_detail_rows_pending:
        for row in doc.items:
            if row.case_detail and not row.so_detail:
                cd_values = case_dict.get(row.case_detail)
                if cd_values:
                    logger.info('ENTERED IF CD_VALUES')
                    row.price_list_rate = cd_values['price_list_rate']
                    row.base_price_list_rate = cd_values['base_price_list_rate']
                    row.discount_percentage = cd_values['discount_percentage']
                    row.discount_amount = cd_values['discount_amount']
                    row.rate = cd_values['rate']
                    row.price_list = cd_values['price_list']
                else:
                    logger.error('Case Number '+row.case_detail+' not found in case_dict dictionary')

    # Section 1 continuation:
    # Iterate through all product bundles, convert 'batches' json to array - 'product_batches'
    # Inside iteration, check if 'product_batches' is a subset of 'master_batches'
    for row in doc.case_details:
        bundle_batches_json_string = row.batches
        bundle_batches = json.loads(bundle_batches_json_string)
        missing_batches = set()

        for b in bundle_batches:
            if b not in master_batches:
                missing_batches.add(b)

        if len(missing_batches) != 0:
            frappe.throw(_("Batches "+str(missing_batches)+" From Bundle "+str(row.case_detail)+" Not Present in Items Table"))
    

    logger.info("CALCULATE TAXES AND TOTALS")
    doc.run_method("calculate_taxes_and_totals")


def update_case_detail(doc, status):

    for row in doc.case_details:
        if (row.case_detail):
            frappe.db.set_value("Case Detail", row.case_detail, "status", status)
