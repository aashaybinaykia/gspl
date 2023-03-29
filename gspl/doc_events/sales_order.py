
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.get_item_details import get_item_details

from frappe.utils import logger
import json
import ast

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

def update_prices(ic, comp, cust, curr, pl, td, prj):
    arguments = {
        	"item_code": ic,
	        "warehouse": None,
            "company": comp,
	        "customer": cust,
	        "conversion_rate": 1.0,
	        "selling_price_list": pl,
	        "price_list_currency": curr,
	        "plc_conversion_rate": 1.0,
	        "doctype": "Sales Order",
	        "name": "",
	        "supplier": None,
	        "transaction_date": td,
	        "conversion_rate": 1.0,
	        "buying_price_list": None,
	        "is_subcontracted": 0,
	        "ignore_pricing_rule": 0,
	        "project": prj,
	        "set_warehouse": ""
            }
    ret_val = get_item_details(arguments)

    price_list_rate = ret_val.price_list_rate
    discount_percentage = 0
    discount_amount = 0
    if ret_val.discount_percentage > 0:
        discount_percentage = ret_val.discount_percentage
        discount_amount = (price_list_rate*discount_percentage)/100
    elif price_list_rate > 0:
        discount_amount = ret_val.discount_amount
        discount_percentage = (discount_amount/price_list_rate)*100

    return price_list_rate, discount_percentage, discount_amount

@frappe.whitelist()
def populate_order_item(item_code, company, customer, currency, price_list, date, project):

    order_item = frappe.db.get_value('Item', item_code, fieldname=['item_code','has_variants','has_batch_no','batch_qty','item_name','description','stock_uom','gst_hsn_code'], as_dict=1)
    if order_item: 
        if order_item['has_variants'] == 0:
            plr, dp, da = update_prices(item_code, company, customer, currency, price_list, date, project)
            items_json_str = json.dumps(order_item)
        else:
            items_list = frappe.db.get_list('Item', filters={'variant_of': item_code}, fields=['item_code','has_variants','has_batch_no','batch_qty','item_name','description','stock_uom','gst_hsn_code'], page_length=18)
            if items_list[0]:
                sample_item = items_list[0]
                plr, dp, da = update_prices(sample_item['item_code'], company, customer, currency, price_list, date, project)
                items_json_str = json.dumps(items_list)
            else:
                frappe.throw("No variants available for template "+item_code)

    ret_dict = {}
    ret_dict['price_list_rate'] = plr
    ret_dict['discount_percentage'] = dp
    ret_dict['discount_amount'] = da
    ret_dict['items'] = items_json_str
    ret_dict['final_rate'] = plr - da
    
    return ret_dict

@frappe.whitelist
def before_validate(doc, method):

    logger.debug("IN NEW VALIDATE")

    for row in doc.order_entry_items:
        qty = row.qty
        item_details = row.items
        no_of_items = item_details.length
        logger.debug(qty+"; "+no_of_items)
        logger.debug(item_details) 

        for i in item_details:
            logger.debug("ITEM DETAILS I: "+str(i))



