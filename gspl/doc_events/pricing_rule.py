
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.naming import parse_naming_series
from frappe.utils import cint, flt

from erpnext.stock.doctype.batch.batch import get_batch_qty
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

from erpnext.stock.doctype.batch.batch import get_batch_qty

from frappe.utils import logger
import json

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)




@frappe.whitelist()
def validate(doc, method):

    if frappe.db.exists(doc.doctype, doc.name) and frappe.db.get_value(doc.doctype, doc.name, 'disable') == doc.disable:
        frappe.throw("Cannot Change Price Rule. Please Delete and Recreate")

    title_parts = []

    # Get values from item, item groups, brands, and item codes

    for item_group in doc.get("item_groups"):
        if item_group.item_group:
            title_parts.append(item_group.item_group)

    for brand in doc.get("brands"):
        if brand.brand:
            title_parts.append(brand.brand)

    for item_code in doc.get("items"):
        if item_code.item_code:
            title_parts.append(item_code.item_code)

    # Get values from customer, customer group, territory, sales partner, campaign, and price list
    for field in ["customer", "customer_group", "territory", "sales_partner", "campaign", "for_price_list"]:
        value = doc.get(field)
        if value:
            title_parts.append(value)

    # Concatenate title parts
    doc.title = " ".join(title_parts)

