# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.stock.utils import get_stock_balance
from frappe.utils import getdate, add_months
from datetime import datetime, timedelta

def execute(filters=None):
    from_date = getdate(filters.get("from_date"))
    to_date = getdate(filters.get("to_date"))
    brand = filters.get("brand")
    group_by = filters.get("group_by")

    results = []
    warehouses = [d.name for d in frappe.get_all('Warehouse')]

    if group_by == "Month":
        current_date = from_date
        while current_date <= to_date:
            current_month_start = datetime(current_date.year, current_date.month, 1)
            current_month_end = add_months(current_month_start, 1) - timedelta(days=1)
            total_purchase = get_total_purchase(from_date=current_month_start, to_date=current_month_end, brand=brand)
            total_sale = get_total_sale(from_date=current_month_start, to_date=current_month_end, brand=brand)
            total_stock = get_total_stock(to_date=current_month_end, brand=brand)
            results.append([current_date.strftime("%Y-%m"), total_purchase, total_sale, total_stock])
            current_date = add_months(current_date, 1)
    elif group_by in ["Item Group", "Brand"]:
        group_values = [d.name for d in frappe.get_all(group_by)]
        for group_value in group_values:
            total_purchase = get_total_purchase(from_date=from_date, to_date=to_date, brand=brand, group_by=group_by, group_value=group_value)
            total_sale = get_total_sale(from_date=from_date, to_date=to_date, brand=brand, group_by=group_by, group_value=group_value)
            total_stock = get_total_stock(to_date=to_date, brand=brand, group_by=group_by, group_value=group_value)
            results.append([group_value, total_purchase, total_sale, total_stock])

    columns = [f"Group:120", "Total Purchase:Currency:120", "Total Sales:Currency:120", "Stock:Float:120"]

    return columns, results

def get_total_purchase(**kwargs):
    conditions = get_conditions(kwargs)
    return frappe.db.sql("""
        SELECT SUM(pi_item.amount)
        FROM `tabPurchase Invoice Item` AS pi_item
        JOIN `tabItem` AS item ON item.name = pi_item.item_code
        JOIN `tabPurchase Invoice` AS pi ON pi.name = pi_item.parent
        WHERE pi.docstatus = 1 AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
    """.format(conditions=conditions), kwargs)[0][0] or 0.0

def get_total_sale(**kwargs):
    conditions = get_conditions(kwargs)
    return frappe.db.sql("""
        SELECT SUM(si_item.amount)
        FROM `tabSales Invoice Item` AS si_item
        JOIN `tabItem` AS item ON item.name = si_item.item_code
        JOIN `tabSales Invoice` AS si ON si.name = si_item.parent
        WHERE si.docstatus = 1 AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s {conditions}
    """.format(conditions=conditions), kwargs)[0][0] or 0.0

def get_total_stock(**kwargs):
    total_stock_qty = 0.0
    total_stock_val = 0.0
    to_date = kwargs.get('to_date')

    conditions = get_conditions(kwargs)
    items = frappe.db.sql(f"""
        SELECT item.name 
        FROM `tabItem` AS item
        WHERE 1=1 {conditions}
    """, kwargs)

    for item in items:
        total_stock = get_stock_balance(item[0], None, to_date, with_valuation_rate=True)
        total_stock_qty += total_stock[0]
        total_stock_val += total_stock[1]
        
    return total_stock_qty



def get_conditions(kwargs):
    conditions = []
    if kwargs.get('brand'):
        conditions.append('AND item.brand = %(brand)s')
    if kwargs.get('group_by') and kwargs.get('group_value') and kwargs.get('group_by') != "Month":
        conditions.append(f"AND item.{kwargs.get('group_by').lower().replace(' ', '_')} = %(group_value)s")
    return " ".join(conditions)
