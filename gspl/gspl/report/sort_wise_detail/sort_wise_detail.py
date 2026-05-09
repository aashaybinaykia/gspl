# Copyright (c) 2026, GSPL
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import cint, flt
from frappe.query_builder.functions import Sum, Count

def execute(filters=None):
    if not filters or not filters.get("item"):
        return [], []

    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "variant",
            "label": _("Variant"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 180
        },
        {
            "fieldname": "shade",
            "label": _("Shades"),
            "fieldtype": "Data",
            "width": 150
        },
        {
            "fieldname": "current_stock",
            "label": _("Current Stock (Meters)"),
            "fieldtype": "Float",
            "width": 160
        },
        {
            "fieldname": "total_batches",
            "label": _("Total Batches"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "sl_batches",
            "label": _("Batches in SL"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "remaining_batches",
            "label": _("Remaining Batches"),
            "fieldtype": "Int",
            "width": 140
        }
    ]

def get_data(filters):
    sort_item = filters.get("item")
    warehouse = filters.get("warehouse")
    
    # 1. Fetch Variants
    variants = frappe.get_all(
        "Item", 
        filters={"variant_of": sort_item, "disabled": 0},
        pluck="name"
    )
    
    if not variants:
        variants = [sort_item]

    # 2. Fetch Shade Attributes
    attributes = frappe.get_all(
        "Item Variant Attribute",
        filters={"parent": ["in", variants]},
        fields=["parent", "attribute_value"]
    )
    shade_map = {}
    for attr in attributes:
        shade_map.setdefault(attr.parent, []).append(attr.attribute_value)

    # 3. Fetch Current Stock 
    bin_table = frappe.qb.DocType("Bin")
    stock_query = (
        frappe.qb.from_(bin_table)
        .select(bin_table.item_code, Sum(bin_table.actual_qty).as_("qty"))
        .where(bin_table.item_code.isin(variants))
    )
    if warehouse:
        stock_query = stock_query.where(bin_table.warehouse == warehouse)
        
    bin_data = stock_query.groupby(bin_table.item_code).run(as_dict=True)
    stock_map = {row.item_code: row.qty for row in bin_data}

    # 4. Fetch Total Active Batches (Upgraded to use Stock Ledger Entry for strict Warehouse filtering)
    sle = frappe.qb.DocType("Stock Ledger Entry")
    batch_query = (
        frappe.qb.from_(sle)
        .select(sle.item_code, sle.batch_no)
        .where(sle.item_code.isin(variants))
        .where(sle.is_cancelled == 0)
        .where(sle.batch_no.isnotnull())
        .where(sle.batch_no != "")
    )
    if warehouse:
        batch_query = batch_query.where(sle.warehouse == warehouse)

    # Group by item and batch, and only count if the batch has positive stock in that warehouse
    batch_query = (
        batch_query
        .groupby(sle.item_code, sle.batch_no)
        .having(Sum(sle.actual_qty) > 0)
    )
    batch_data = batch_query.run(as_dict=True)
    
    total_batch_map = {}
    for row in batch_data:
        total_batch_map[row.item_code] = total_batch_map.get(row.item_code, 0) + 1

    # 5. Fetch Batches in Short Length (SL) Cases (Upgraded to count distinct parents)
    sl_batch_map = {}
    sl_case_filters = {"enabled": 1, "contents": "Short Length"}
    if warehouse:
        sl_case_filters["warehouse"] = warehouse
        
    sl_cases = frappe.get_all(
        "Case Detail",
        filters=sl_case_filters,
        pluck="name"
    )
    
    if sl_cases:
        cd_item = frappe.qb.DocType("Case Detail Item")
        sl_query = (
            frappe.qb.from_(cd_item)
            .select(cd_item.item_code, Count(cd_item.parent).distinct().as_("count"))
            .where(cd_item.parent.isin(sl_cases))
            .where(cd_item.item_code.isin(variants))
            .groupby(cd_item.item_code)
        )
        sl_items = sl_query.run(as_dict=True)
        sl_batch_map = {row.item_code: row.count for row in sl_items}

    # 6. Construct Final Data 
    data = []
    for variant in variants:
        total_batches = cint(total_batch_map.get(variant, 0))
        sl_batches = cint(sl_batch_map.get(variant, 0))
        current_stock = flt(stock_map.get(variant, 0.0))
        
        data.append({
            "variant": variant,
            "shade": ", ".join(shade_map.get(variant, [])),
            "current_stock": current_stock,
            "total_batches": total_batches,
            "sl_batches": sl_batches,
            "remaining_batches": total_batches - sl_batches
        })

    return data