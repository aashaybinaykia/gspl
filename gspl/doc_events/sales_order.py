
from __future__ import unicode_literals

import frappe
from frappe import _

from erpnext.stock.get_item_details import get_item_details

from frappe.utils import logger
import json
import ast

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api_so", allow_site=True, file_count=50)

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
    else:
        discount_amount = ret_val.discount_amount

    return price_list_rate, discount_percentage, discount_amount

def add_child_to_so(doc, item, details):
    if details.get('has_batch_no') == 1 and details.get('batch_qty') > 0:
        qty = details.get('batch_qty') * item.qty
    elif details.get('has_batch_no') == 0:
        qty = item.qty
    else:
        qty = 8 * item.qty
    child = doc.append('items', {})
    child.item_code = details.get('item_code')
    child.qty = qty
    child.discount_amount = item.discount_amount
    child.discount_percentage = item.discount_percentage
    child.rate = item.final_rate
    child.price_list = item.price_list
    if item.price_list_rate > 0:
        child.price_list_rate = item.price_list_rate
    else:
        frappe.throw("Rate is o for "+details.get('item_code'))
    child.delivery_date = doc.delivery_date
    child.item_name = details.get('item_name')
    child.description = details.get('description')
    child.uom = details.get('stock_uom')
    child.gst_hsn_code = details.get('gst_hsn_code')

@frappe.whitelist()
def populate_order_item(item_code, company, customer, currency, price_list, date, project):

    order_item = frappe.db.get_value('Item', item_code, fieldname=['item_code','has_variants','has_batch_no','batch_qty','item_name','description','stock_uom','gst_hsn_code','brand'], as_dict=1)
    if order_item: 
        

        if order_item['has_variants'] == 0:
            plr, dp, da = update_prices(item_code, company, customer, currency, price_list, date, project)
            brand = order_item['brand']
            items_json_str = json.dumps(order_item)
        else:
            items_list = frappe.db.get_list('Item', filters={'variant_of': item_code}, fields=['item_code','has_variants','has_batch_no','batch_qty','item_name','description','stock_uom','gst_hsn_code','brand'], page_length=18)
            if items_list[0]:
                sample_item = items_list[0]
                plr, dp, da = update_prices(sample_item['item_code'], company, customer, currency, price_list, date, project)
                brand = sample_item['brand']
                items_json_str = json.dumps(items_list)
            else:
                frappe.throw("No variants available for template "+item_code)

    ret_dict = {}
    ret_dict['price_list_rate'] = plr
    ret_dict['discount_percentage'] = dp
    ret_dict['discount_amount'] = da
    ret_dict['items'] = items_json_str
    ret_dict['final_rate'] = plr - da
    ret_dict['brand'] = brand
    
    return ret_dict




@frappe.whitelist()
def before_validate(doc, method):
    doc.items.clear()
    for row in doc.order_entry_items:
        item_details = json.loads(row.items)
        if type(item_details) == list:
            length = len(item_details)
            for i in range(length):
                details = item_details[i]
                add_child_to_so(doc, row, details)
        else:
            add_child_to_so(doc, row, item_details)

    # doc.run_method("calculate_taxes_and_totals")









