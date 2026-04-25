from __future__ import unicode_literals

import frappe
from frappe import _
import requests
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content

def update_purchase_invoice_items(doc):
    """
    Update Purchase Invoice Items based on scan_case (Google Sheet Link).
    Fetches Case Detail Items and applies Rates based on Case + Batch combinations.
    """

    if not doc.scan_case:
        frappe.throw(_("Scan Case (Google Sheet Link) is required."))

    # 1. **Extract Default Data from the First Row of Items Table**
    if not doc.items:
        frappe.throw(_("No items found in the Purchase Invoice."))

    first_item = doc.items[0]  
    default_data = {field: getattr(first_item, field) for field in first_item.as_dict().keys()}

    # 2. **Fetch CSV Data from Google Sheets using Frappe Utility**
    try:
        content = get_csv_content_from_google_sheets(doc.scan_case)
        data = read_csv_content(content)  
    except Exception as e:
        frappe.throw(_("Failed to fetch Google Sheet data: {}").format(str(e)))

    if not data or len(data) < 2:
        frappe.throw(_("Google Sheet is empty or not formatted correctly."))

    # 3. **Convert CSV Data into a Dictionary mapped by (Case, Batch)**
    keys = [str(k).strip().lower() for k in data[0]]  
    
    case_col_name = "case no" if "case no" in keys else ("case detail" if "case detail" in keys else None)
    
    if not case_col_name or "batch" not in keys or "rate" not in keys:
        frappe.throw(_("Google Sheet must contain 'case no' (or 'case detail'), 'batch', and 'rate' columns."))

    case_col_idx = keys.index(case_col_name)
    batch_col_idx = keys.index("batch")
    rate_col_idx = keys.index("rate")

    batch_rate_data = {}  
    cases_to_process = set() 

    for row in data[1:]:  
        if len(row) <= max(case_col_idx, batch_col_idx, rate_col_idx):
            continue 
            
        case_no = str(row[case_col_idx]).strip()
        batch_no = str(row[batch_col_idx]).strip()
        rate_val = row[rate_col_idx]
        
        if case_no and batch_no and rate_val:
            try:
                batch_rate_data[(case_no, batch_no)] = float(rate_val)
                cases_to_process.add(case_no)
            except ValueError:
                frappe.throw(_("Invalid rate format in Google Sheet for Case: {}, Batch: {}").format(case_no, batch_no))

    if not batch_rate_data:
        frappe.throw(_("No valid Case, Batch, and Rate data found in Google Sheet."))

    # 4. **Delete all existing rows in the Purchase Invoice Items table**
    doc.items = []
    doc.set("items", doc.items) 

    # 5. **Fetch Case Detail Items & Rebuild Purchase Invoice Items Table**
    for case_number in cases_to_process:
        if not frappe.db.exists("Case Detail", case_number):
            frappe.throw(_("Case Detail {} not found").format(case_number))

        case_detail = frappe.get_doc("Case Detail", case_number)

        if not case_detail.items:
            frappe.throw(_("No items found in Case Detail: {}").format(case_number))

        for case_item in case_detail.items:
            item_batch = str(case_item.batch_no or "").strip()
            rate = batch_rate_data.get((case_number, item_batch))

            if rate is None:
                frappe.throw(_("Rate missing in Google Sheet for Case: {0}, Batch: {1}").format(case_number, item_batch))

            new_item = default_data.copy()
            
            # --- FIX: Remove Frappe system fields to prevent Duplicate Primary Key Error ---
            system_fields = ["name", "parent", "parenttype", "parentfield", "idx", "creation", "modified"]
            for field in system_fields:
                new_item.pop(field, None)

# Fetch BOTH the actual item name and HSN code from the Item master
            item_details = frappe.db.get_value("Item", case_item.item_code, ["item_name", "gst_hsn_code"], as_dict=True)
            actual_item_name = item_details.item_name if item_details else case_item.item_code
            actual_hsn_code = item_details.gst_hsn_code if item_details else None

            new_item = default_data.copy()
            
            # Remove Frappe system fields to prevent Duplicate Primary Key Error
            system_fields = ["name", "parent", "parenttype", "parentfield", "idx", "creation", "modified"]
            for field in system_fields:
                new_item.pop(field, None)

            new_item.update({
                "item_code": case_item.item_code,
                "item_name": actual_item_name,           # <--- Fixed
                "gst_hsn_code": actual_hsn_code,         # <--- Fixed
                "qty": -case_item.qty if doc.is_return else case_item.qty,  
                "description": case_item.description,
                "uom": case_item.uom,
                "batch_no": case_item.batch_no,
                "rate": rate,
                "received_qty": -case_item.qty if doc.is_return else case_item.qty,
                "case_number": case_number
            })

            doc.append("items", new_item)

    # **Save & Validate Items**
    doc.set("items", doc.items)  

    frappe.msgprint(_("Purchase Invoice Items updated successfully based on Case and Batch rates."))

@frappe.whitelist()
def validate(doc, method):
    if doc.update_stock and not doc.is_return:
        validate_if_case_details_exists(doc)

def before_validate(doc,method):
    if doc.is_return and doc.scan_case:
        update_purchase_invoice_items(doc)

@frappe.whitelist()
def on_submit(doc, method):
    if doc.update_stock and not doc.is_return:
        create_case_details(doc)
    
@frappe.whitelist()
def before_cancel(doc, method):
    if doc.update_stock and not doc.is_return:
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
        case = frappe.new_doc("Case Detail")
        case.new_item_code = case_number
        case.warehouse = warehouse

        for row in items:
            case.append('items', {
                'item_code': row.item_code,
                'qty': row.qty,
                'description': row.description,
                'rate': row.rate,
                'uom': row.uom,
                'batch_no': row.batch_no,
            })

        case.save()

def delete_case_details(doc):
    cases = list(set([row.case_number for row in doc.items if row.case_number and not row.purchase_receipt]))
    for case_number in cases:
        case = frappe.get_doc("Case Detail", case_number)
        case.delete()

def get_naming_series(doc):
    naming_series = None
    if doc.is_return:
        if not doc.set_posting_time:
            naming_series = "PRET-.FY.-"
        else:
            return naming_series
    else:
        if doc.items:
            brand = doc.items[0].brand
            if brand:
                if brand in ["Arvind", "Trendy"]:
                    naming_series = "P-.FY.-AR-.####"
                elif brand in ["Vimal", "GG"]:
                    naming_series = "P-.FY.-RE-.####"
                elif brand == "Mozzini":
                    naming_series = "P-.FY.-MZ-.####"
                elif brand == "BRFL":
                    naming_series = "P-.FY.-BR-.####"
    return naming_series

@frappe.whitelist()
def autoname(doc, method):
    naming_series = get_naming_series(doc)
    if naming_series:
        doc.naming_series = naming_series