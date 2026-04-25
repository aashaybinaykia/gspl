# Copyright (c) 2024, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {
            "fieldname": "bundle_type",
            "label": _("Bundle Type"),
            "fieldtype": "Link",
            "options": "Item",
            "width": 200
        },
        {
            "fieldname": "brand",
            "label": _("Brand"),
            "fieldtype": "Link",
            "options": "Brand",
            "width": 150
        },
        {
            "fieldname": "item_group",
            "label": _("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
            "width": 150
        },
        {
            "fieldname": "total_cases",
            "label": _("Total Cases"),
            "fieldtype": "Int",
            "width": 120
        },
        {
            "fieldname": "total_qty",
            "label": _("Total Quantity"),
            "fieldtype": "Float",
            "width": 120
        },
        {
            "fieldname": "super_net_rate",
            "label": _("Super Net Rate"),
            "fieldtype": "Currency",
            "options": "currency",
            "width": 130
        }
    ]

def get_data(filters):
    conditions = ""
    
    if filters:
        # 1. Exact Match Fields
        exact_fields = ["bundle_type", "status", "warehouse", "brand", "item_group", "contents"]
        for field in exact_fields:
            if filters.get(field):
                conditions += f" AND {field} = %({field})s"

        # 2. Checkbox Field
        if "enabled" in filters:
            conditions += " AND enabled = %(enabled)s"

        # 3. Partial Match Fields
        if filters.get("new_item_code"):
            conditions += " AND new_item_code LIKE %(new_item_code)s"
            filters["new_item_code"] = f"%{filters.get('new_item_code')}%"
            
        if filters.get("rack"):
            conditions += " AND rack LIKE %(rack)s"
            filters["rack"] = f"%{filters.get('rack')}%"

    query = f"""
        SELECT 
            bundle_type, 
            brand,
            item_group,
            COUNT(name) as total_cases,
            SUM(total_qty) as total_qty
        FROM 
            `tabCase Detail`
        WHERE 
            1=1 {conditions}
            AND bundle_type IS NOT NULL
        GROUP BY 
            bundle_type, brand, item_group
        ORDER BY 
            total_cases DESC
    """
    
    data = frappe.db.sql(query, filters, as_dict=1)

    # Fetch Super Net Rates and map them to the results
    if data:
        bundle_types = [row.bundle_type for row in data if row.bundle_type]
        
        if bundle_types:
            # Get latest Super Net prices for these items
            item_prices = frappe.get_all(
                'Item Price',
                filters={
                    'item_code': ['in', bundle_types],
                    'price_list': 'Super Net'
                },
                fields=['item_code', 'price_list_rate'],
                order_by='valid_from desc'
            )

            # Map the first (latest) price found for each item
            price_map = {}
            for price in item_prices:
                if price.item_code not in price_map:
                    price_map[price.item_code] = price.price_list_rate

            # Inject the rate into the final data rows
            for row in data:
                row['super_net_rate'] = price_map.get(row.bundle_type, 0.0)

    return data