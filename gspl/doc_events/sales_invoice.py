from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.naming import parse_naming_series

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def autoname(doc, method):
    if doc.is_return:
        # Use .get() to safely check the reason
        reason = doc.get("reason_for_issuing_document")
        if reason == "01-Sales Return" or not reason:
            doc.naming_series = "SR-.FY.-."
        else:
            doc.naming_series = "CN-.FY.-"

@frappe.whitelist()
def validate(doc, method):
    # Check if the document is being cancelled
    if doc.docstatus == 2:  # 2 means Cancelled in ERPNext
        # Use .get() to safely check for IRN
        if doc.get("irn"):
            frappe.throw(_("You cannot cancel this Sales Invoice as IRN is generated."))

@frappe.whitelist()
def before_validate(doc, method):
    if doc.is_return and not doc.return_against and not doc.update_stock:
        set_against_return(doc)
    
    # Use .get() to prevent AttributeError on missing fields
    if not doc.get("reason_for_issuing_document") == "01-Sales Return":
        doc.update_billed_amount_in_sales_order = False

def set_against_return(doc):
    # Added a safety check to ensure items exist before accessing index 0
    if doc.items and doc.items[0].delivery_note:
        return_against = frappe.db.get_value('Delivery Note', {'name': doc.items[0].delivery_note}, 'return_against')
        sales_invoice_name = frappe.db.get_value('Sales Invoice Item',
                                         filters={
                                             'delivery_note': return_against,
                                             'qty': ['>',0]
                                             },
                                         fieldname='parent',
                                         as_dict=False)
        if sales_invoice_name:
            doc.return_against = sales_invoice_name
        else:
            frappe.throw(_("Either Create Sales Invoice or Cancel Delivery Note"))