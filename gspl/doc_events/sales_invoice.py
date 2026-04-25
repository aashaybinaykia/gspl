
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.naming import parse_naming_series

from erpnext.stock.doctype.batch.batch import get_batch_qty


@frappe.whitelist()
def autoname(doc, method):
    if doc.is_return:
        if doc.reason_for_issuing_document == "01-Sales Return" or doc.reason_for_issuing_document == "":
            doc.naming_series = "SR-.FY.-."
        else:
            doc.naming_series = "CN-.FY.-"
    # if doc.naming_series == "SI-.FY.-.{series_number}" or doc.naming_series == "SR-.FY.-.{series_number}":
    #     doc.name = parse_naming_series(doc.naming_series, doc=doc)
@frappe.whitelist()
def validate(doc, method):
    # Check if the document is being cancelled
    if doc.docstatus == 2:  # 2 means Cancelled in ERPNext
        # Check if IRN field is populated
        if doc.irn:
            frappe.throw(_("You cannot cancel this Sales Invoice as IRN is generated."))

@frappe.whitelist()
def before_validate(doc, method):
    if doc.is_return and not doc.return_against and not doc.update_stock:
        set_against_return(doc)
    if  not doc.reason_for_issuing_document == "01-Sales Return":
        doc.update_billed_amount_in_sales_order = False

    # for item in doc.items:
    #     is_stock_item = frappe.db.get_value('Item',
    #                                         filters={
    #                                             'item_code': item
    #                                         },
    #                                         fieldname = 'is_stock_item',
    #                                         as_dict = False)
        
    #     if is_stock_item and not item.delivery_note:
    #         frappe.throw("No Delivery Note")

def set_against_return(doc):
    if doc.items[0].delivery_note:
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


