import frappe
from frappe.utils import flt

@frappe.whitelist()
def process_custom_barcode(barcode, sales_order=None, company=None, customer=None):
    # 1. Resolve Barcode strictly as a Batch ID or Item Code
    batch_info = frappe.db.get_value("Batch", barcode, ["item", "name", "batch_qty"], as_dict=True)
    
    if batch_info:
        item_code = batch_info.item
        batch_no = batch_info.name
        batch_qty = batch_info.get("batch_qty") or 1 
            
    else:
        if frappe.db.exists("Item", barcode):
            item_code = barcode
            batch_no = None
            batch_qty = 1 
        else:
            frappe.throw(f"Invalid Scan: '{barcode}' does not match any existing Batch or Item Code.")

    # 2. SO PRIORITY: Fetch exact rates and requested fields
    if sales_order and item_code:
        so_item = frappe.db.get_value(
            "Sales Order Item",
            {"parent": sales_order, "item_code": item_code},
            [
                "price_list_rate", "rate", "discount_percentage", "uom", 
                "conversion_factor", "name", 
                "item_name", "brand", "stock_uom", "price_list"
            ],
            as_dict=True
        )

        if so_item:
            return {
                "item_code": item_code, 
                "batch_no": batch_no,
                "qty": batch_qty, 
                "use_serial_batch_fields": 1, 
                
                "item_name": so_item.item_name,
                "brand": so_item.brand,
                "stock_uom": so_item.stock_uom,
                "price_list": so_item.price_list, 
                "price_list_rate": so_item.price_list_rate,
                "rate": so_item.rate,
                "discount_percentage": so_item.discount_percentage,
                "ignore_pricing_rule": 1, 
                "uom": so_item.uom,
                "conversion_factor": so_item.conversion_factor,
                "against_sales_order": sales_order,
                "so_detail": so_item.name,
                "is_from_so": True
            }

    # 3. IF VALID ITEM/BATCH BUT NO SO ITEM FOUND: Trigger standard fallback
    return {"fallback_to_standard": True}