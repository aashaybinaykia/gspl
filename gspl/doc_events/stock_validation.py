import frappe
from frappe import _

def prevent_locked_batch_transfer(doc, method):
    # 1. Global Bypass (For Case Detail Transfers)
    if getattr(doc, "case_detail_transfer", None) or doc.flags.ignore_case_lock:
        return

    # 2. Row-Level Validation (For Delivery Notes, Stock Entries, Sales Invoices)
    for row in doc.items:
        if row.get("batch_no"):
            
            # BYPASS: If this row is officially linked to a Case Detail, allow it to be sold.
            if getattr(row, "case_detail", None):
                continue
                
            # STRICT BLOCK: If it is a manual entry without a case link, check the lock.
            is_locked = frappe.db.get_value("Batch", row.batch_no, "custom_locked_by_case_detail")
            if is_locked:
                frappe.throw(_("Row #{0}: Batch {1} is locked by an Active Case Detail and cannot be manually transferred or sold.").format(row.idx, row.batch_no))