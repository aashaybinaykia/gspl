
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def validate(doc, method):
    if doc.update_stock:
        validate_if_case_details_exists(doc)

@frappe.whitelist()
def on_submit(doc, method):
    if doc.update_stock:
        create_case_details(doc)

@frappe.whitelist()
def before_cancel(doc, method):
    if doc.update_stock:
        delete_case_details(doc)


def validate_if_case_details_exists(doc):    
    for row in doc.items:
        if row.case_number and not row.purchase_receipt:
            if frappe.db.exists("Case Detail", row.case_number):
                frappe.throw(_(
                    "Row #%s: Case %s already exists for item %s. " 
                    "Please use different Case ID" % (
                        row.idx, row.case_number, row.item_name,)))


def create_case_details(doc):
    case_detail = {}
    for row in doc.items:
        if row.case_number and not row.purchase_receipt:
            key = (row.case_number, row.warehouse)
            case_detail.setdefault(key, [])
            case_detail[key].append(row)


    for (case_number, warehouse), items in case_detail.items():
        # item = frappe.get_doc(dict(
        #         doctype = "Item",
        #         item_code = product_bundle_id,
        #         item_name = product_bundle_id,
        #         item_group = item_group,
        #         brand = brand,
        #         is_stock_item = False,
        #         has_batch_no = False,
        #         stock_uom = "Nos",
        #         # is_sales_item = True,
        #     )).insert()

        # case = frappe.get_doc(dict(
        #         doctype = "Case Detail",
        #         new_item_code = case_number,
        #         warehouse = warehouse
        #     )).insert()
        # last_case = frappe.get_last_doc("Case Detail")
        # frappe.throw(_(
        #     "Row #%s: Case %s already exists for item %s. " 
        #     "Please use different Case ID" % (
        #         last_case, row.case_number, row.item_name,)))
        case = frappe.new_doc("Case Detail")
        case.new_item_code = case_number
        case.warehouse = warehouse

        for row in items:
            # Mark Batch as disabled
            # frappe.db.set_value("Batch", row.batch_no, 'disabled', True)

            case.append('items', {
                'item_code': row.item_code,
                'qty': row.qty,
                'description': row.description,
                'rate': row.rate,
                'uom': row.uom,
                'batch_no': row.batch_no,
                # 'brand': row.brand
            })

        case.save()


def delete_case_details(doc):
    cases = list(set([row.case_number for row in doc.items if row.case_number and not row.purchase_receipt]))
    for case_number in cases:
        case = frappe.get_doc("Case Detail", case_number)
        case.delete()
