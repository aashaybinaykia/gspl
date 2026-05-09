
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
def validate(doc, method=None):
    # 1. Basic Initializations using .get() for v16 safety
    if doc.get("is_return"):
        doc.issue_credit_note = 1

    doc.total_batches = len(doc.get("items", []))

    master_batches = set()
    case_dict = {}
    case_detail_rows_pending = False

    # 2. Map Available SO Items into a Dictionary (O(1) Lookup)
    # Streamlined: 1-to-1 mapping since item_codes are unique per SO
    available_so_items = {}
    if doc.get("sales_order"):
        so_doc = frappe.get_doc('Sales Order', doc.sales_order)
        for so_row in so_doc.get("items", []):
            if so_row.qty > so_row.delivered_qty:
                available_so_items[so_row.item_code] = so_row

    # 3. Main Item Iteration
    for row in doc.get("items", []):
        if row.rate == 0:
            frappe.throw(_(f"Item {row.item_code} has a Rate of 0"))

        if row.batch_no:
            master_batches.add(str(row.batch_no))
            
            # Fetch and set real-time warehouse batch quantity
            batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=row.warehouse, item_code=row.item_code)
            if batch_qty > 0:
                row.qty = batch_qty
                row.stock_qty = row.qty * row.conversion_factor             
        
        # Section 3: Link to Sales Order
        if doc.get("sales_order") and not row.so_detail:
            # Direct dictionary lookup
            so_row = available_so_items.get(row.item_code)

            if so_row:
                row.so_detail = so_row.name
                row.against_sales_order = doc.sales_order
                row.price_list_rate = so_row.price_list_rate
                row.base_price_list_rate = so_row.base_price_list_rate
                row.discount_percentage = so_row.discount_percentage
                row.discount_amount = so_row.discount_amount
                row.rate = so_row.rate
                row.price_list = so_row.price_list
                row.pricing_rules = ""

                # Section 4: Cache the Case Detail pricing
                if row.case_detail and row.case_detail not in case_dict:
                    case_dict[row.case_detail] = {
                        'price_list_rate': row.price_list_rate,
                        'base_price_list_rate': row.base_price_list_rate,
                        'discount_percentage': row.discount_percentage,
                        'discount_amount': row.discount_amount,
                        'rate': row.rate,
                        'price_list': row.price_list
                    }
                    
            elif row.case_detail:
                case_detail_rows_pending = True

    # Section 3b: Fallback Case Detail Pricing
    if doc.get("sales_order") and case_detail_rows_pending:
        for row in doc.items:
            if row.case_detail and not row.so_detail:
                cd_values = case_dict.get(row.case_detail)
                if cd_values:
                    for key, value in cd_values.items():
                        row.set(key, value)

    # Section 1 Continuation: Bundle Validation
    for row in doc.get("case_details", []):
        enabled = row.get("enabled") if hasattr(row, "enabled") else frappe.db.get_value("Case Detail", row.name, "enabled")
        
        if enabled and row.get("batches"):
            try:
                bundle_batches = json.loads(row.batches)
                missing_batches = [b for b in bundle_batches if b not in master_batches]

                if missing_batches:
                    frappe.throw(_(f"Batches {missing_batches} from Bundle {row.case_detail} are not present in the Items Table."))
            except json.JSONDecodeError:
                pass 

    doc.run_method("calculate_taxes_and_totals")


def update_case_detail(doc, status):
    for row in doc.case_details:
        if (row.case_detail):
            frappe.db.set_value("Case Detail", row.case_detail, "status", status)
