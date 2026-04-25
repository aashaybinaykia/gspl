
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import nowdate



@frappe.whitelist()
def before_save(doc, method):
	if not doc.valid_upto:
		validate_item_price(doc, method, doc.item_code)
		order_item = frappe.db.get_value('Item', doc.item_code, fieldname=['has_variants'], as_dict=1)
		if order_item: 
			if order_item['has_variants'] == 1:
				items_list = frappe.db.get_list('Item', filters={'variant_of': doc.item_code}, fields=['item_code'], page_length=20000)
				for item in items_list:
					validate_item_price(doc, method, item['item_code'])




def validate_item_price(doc, method, item):
	frappe.db.set_value("Item", item, 'standard_rate', doc.price_list_rate)
	frappe.db.set_value("Item", item, 'price_list',doc.price_list)
            


        