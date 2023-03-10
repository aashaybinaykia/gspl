
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
        master_batches.add(int(row.batch_no))
    
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


def update_case_detail(doc, status):

    for row in doc.case_details:
        if (row.case_detail):
            frappe.db.set_value("Case Detail", row.case_detail, "status", status)
