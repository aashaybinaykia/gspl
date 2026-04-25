# File: gspl_consolidated_stock_ageing.py

import frappe
from frappe import _
from frappe.utils import date_diff, flt

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data(filters)
    return columns, data

def get_columns(filters):
    return [
        {"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
        {"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 150},
        {"label": _("Brand"), "fieldname": "brand", "fieldtype": "Data", "width": 100},
        {"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Data", "width": 100},
        {"label": _("Total Qty"), "fieldname": "total_qty", "fieldtype": "Float", "width": 100},
        {"label": f"0-{filters.range_1} Days", "fieldname": "range_1_qty", "fieldtype": "Float", "width": 100},
        {"label": f"{filters.range_1}-{filters.range_2} Days", "fieldname": "range_2_qty", "fieldtype": "Float", "width": 100},
        {"label": f"{filters.range_2}-{filters.range_3} Days", "fieldname": "range_3_qty", "fieldtype": "Float", "width": 100},
        {"label": f"Above {filters.range_3} Days", "fieldname": "above_range_3_qty", "fieldtype": "Float", "width": 100},
    ]

def get_data(filters):
    # --- OPTIMIZATION START ---
    # 1. Identify items with > 0 Stock FIRST. 
    # Use frappe.db.sql instead of get_all to support GROUP BY and HAVING properly
    
    items_with_stock = frappe.db.sql("""
        SELECT item_code, SUM(actual_qty) as total_stock
        FROM `tabStock Ledger Entry`
        WHERE posting_date <= %s 
          AND is_cancelled = 0 
          AND company = %s
        GROUP BY item_code
        HAVING total_stock > 0
    """, (filters.ask_on_date, filters.company), as_dict=True)

    # Convert to a dictionary for fast lookup: {'ITEM-001': 50.0, 'ITEM-002': 10.0}
    stock_map = {d.item_code: d.total_stock for d in items_with_stock}
    
    if not stock_map:
        return []

    valid_item_codes = list(stock_map.keys())
    # --- OPTIMIZATION END ---

    # 2. Build Item Filters (Brand, Item Group) + Valid Stock Items
    # We filter the 'name' by the list of items that actually have stock
    item_filters = {"name": ["in", valid_item_codes]}
    
    if filters.get("item_group"):
        item_filters["item_group"] = filters.get("item_group")
    if filters.get("brand"):
        item_filters["brand"] = filters.get("brand")

    # Fetch details only for items that have stock AND match user filters
    items = frappe.get_all("Item", 
        filters=item_filters,
        fields=["name", "item_name", "brand", "item_group"])

    report_data = []

    for item in items:
        # Get the pre-calculated stock balance
        stock_balance = stock_map.get(item.name, 0.0)

        # 3. Fetch Inward Entries (FIFO Logic)
        # JOIN 'Stock Entry' to filter out 'Material Transfer'
        inward_entries = frappe.db.sql("""
            SELECT 
                sle.posting_date, sle.actual_qty 
            FROM 
                `tabStock Ledger Entry` sle
            LEFT JOIN 
                `tabStock Entry` se ON (sle.voucher_no = se.name AND sle.voucher_type = 'Stock Entry')
            WHERE 
                sle.item_code = %s 
                AND sle.actual_qty > 0 
                AND sle.posting_date <= %s
                AND sle.is_cancelled = 0
                AND sle.company = %s
                # Exclude Material Transfers so we don't reset age on internal movement
                AND (se.purpose IS NULL OR se.purpose != 'Material Transfer')
            ORDER BY 
                sle.posting_date DESC, sle.creation DESC
        """, (item.name, filters.ask_on_date, filters.company), as_dict=True)

        # 4. Consume stock to calculate Ageing
        remaining_qty = flt(stock_balance)
        age_buckets = {"range_1": 0.0, "range_2": 0.0, "range_3": 0.0, "above": 0.0}

        for entry in inward_entries:
            if remaining_qty <= 0:
                break

            consumed_qty = min(remaining_qty, flt(entry.actual_qty))
            age_days = date_diff(filters.ask_on_date, entry.posting_date)

            if age_days <= int(filters.range_1):
                age_buckets["range_1"] += consumed_qty
            elif age_days <= int(filters.range_2):
                age_buckets["range_2"] += consumed_qty
            elif age_days <= int(filters.range_3):
                age_buckets["range_3"] += consumed_qty
            else:
                age_buckets["above"] += consumed_qty

            remaining_qty -= consumed_qty

        # Handle "Ghost Stock" (Rare data mismatches)
        if remaining_qty > 0:
            age_buckets["above"] += remaining_qty

        row = {
            "item_code": item.name,
            "item_name": item.item_name,
            "brand": item.brand,
            "item_group": item.item_group,
            "total_qty": stock_balance,
            "range_1_qty": age_buckets["range_1"],
            "range_2_qty": age_buckets["range_2"],
            "range_3_qty": age_buckets["range_3"],
            "above_range_3_qty": age_buckets["above"]
        }
        report_data.append(row)

    return report_data