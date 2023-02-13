
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname, revert_series_if_last
from frappe.utils import cint, flt, get_link_to_form
from frappe.utils.data import add_days
from frappe.utils.jinja import render_template

from frappe.utils import logger

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)


@frappe.whitelist()   
def custom_get_batch_no(item_code, warehouse, qty=1, throw=False, serial_no=None):
    logger.debug("SEARCH ME HERE BATCH")
    """Do not return any batch number"""
    batch_no = None
    #batches = get_batches(item_code, warehouse, qty, throw, serial_no)

    #for batch in batches:
    #    if flt(qty) <= flt(batch.qty):
    #       batch_no = batch.batch_id
    #       break
    
    if not batch_no:
        frappe.msgprint(
            _(
                "Please select a Batch for Item {0}."
                ).format(frappe.bold(item_code))
        )
        if throw:
            raise UnableToSelectBatchError
            
    return batch_no
