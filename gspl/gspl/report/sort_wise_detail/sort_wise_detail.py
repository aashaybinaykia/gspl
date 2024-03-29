# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns(filters.item)
	data = get_data(filters)
	return columns, data


def get_columns(item):
	columns = [
		{
			"fieldname": "variant_name",
			"label": _("Variant"),
			"fieldtype": "Link",
			"options": "Item",
			"width": 200,
		}
	]

	item_doc = frappe.get_doc("Item", item)

	for entry in item_doc.attributes:
		columns.append(
			{
				"fieldname": frappe.scrub(entry.attribute),
				"label": entry.attribute,
				"fieldtype": "Data",
				"width": 100,
			}
		)

	additional_columns = [
		{
			"fieldname": "current_stock", 
			"label": _("Current Stock"), 
			"fieldtype": "Float", 
			"width": 120
		},
		{
			"fieldname": "total_batches", 
			"label": _("Total Batches"), 
			"fieldtype": "Float", 
			"width": 120
		},
		{
			"fieldname": "sl_batches", 
			"label": _("Batches in SL"), 
			"fieldtype": "Float", 
			"width": 120
		},
		{
			"fieldname": "remaining_batches", 
			"label": _("Remaining Batches"), 
			"fieldtype": "Float", 
			"width": 120
		},
		{
			"fieldname": "open_orders",
			"label": _("Open Sales Orders"),
			"fieldtype": "Float",
			"width": 150,
		},
		{
			"fieldname": "open_orders_for_batch",
			"label": _("Open Sales Orders (Batches)"),
			"fieldtype": "Float",
			"width": 150,
		},
	]
	columns.extend(additional_columns)

	return columns


def get_data(filters):
	item = filters.item
	warehouse = None

	if not item:
		return []
	
	if filters.get('warehouse'):
		warehouse = filters.get('warehouse')
	item_dicts = []

	variant_results = frappe.db.get_all(
		"Item", fields=["name"], filters={"variant_of": ["=", item], "disabled": 0}
	)

	if not variant_results:
		# frappe.msgprint(_("There aren't any item variants for the selected item"))
		# return []
		variant_results = frappe.db.get_all(
			"Item", fields=["name"], filters={"name": ["=", item], "disabled": 0}
		)
	# else:
	# 	variant_list = [variant["name"] for variant in variant_results]
	variant_list = [variant["name"] for variant in variant_results]

	order_count_map = get_open_sales_orders_count(variant_list, warehouse)
	batch_order_count_map = get_open_sales_orders_count_for_batche(variant_list, warehouse)
	stock_details_map = get_stock_details_map(variant_list, warehouse)
	batch_details_map = get_batch_details_map(variant_list, warehouse)
	case_details_map = get_case_details_map(variant_list, warehouse)
	attr_val_map = get_attribute_values_map(variant_list)

	attributes = frappe.db.get_all(
		"Item Variant Attribute",
		fields=["attribute"],
		filters={"parent": ["in", variant_list]},
		group_by="attribute",
	)
	attribute_list = [row.get("attribute") for row in attributes]

	# Prepare dicts
	variant_dicts = [{"variant_name": d["name"]} for d in variant_results]
	for item_dict in variant_dicts:
		name = item_dict.get("variant_name")

		for attribute in attribute_list:
			attr_dict = attr_val_map.get(name)
			if attr_dict and attr_dict.get(attribute):
				item_dict[frappe.scrub(attribute)] = attr_val_map.get(name).get(attribute)

		item_dict["open_orders"] = order_count_map.get(name) or 0
		item_dict["open_orders_for_batch"] = batch_order_count_map.get(name) or 0

		if stock_details_map.get(name):
			item_dict["current_stock"] = stock_details_map.get(name)["Inventory"] or 0
		else:
			item_dict["current_stock"] = 0

		if batch_details_map.get(name):
			item_dict["total_batches"] = batch_details_map.get(name)["Total"] or 0
		else:
			item_dict["total_batches"] = 0

		if case_details_map.get(name):
			item_dict["sl_batches"] = case_details_map.get(name) or 0
		else:
			item_dict["sl_batches"] = 0

		item_dict["remaining_batches"] = item_dict["total_batches"] - item_dict["sl_batches"]

		item_dicts.append(item_dict)

	return item_dicts


def get_open_sales_orders_count(variants_list, warehouse=None):
	filters=[
		["Sales Order", "docstatus", "=", 1],
		["Sales Order Item", "item_code", "in", variants_list],
	]

	if warehouse:
		filters.append(["Sales Order Item", "warehouse", "=", warehouse])

	open_sales_orders = frappe.db.get_list(
		"Sales Order",
		fields=["name", "`tabSales Order Item`.item_code"],
		filters=filters,
		distinct=1,
	)

	order_count_map = {}
	for row in open_sales_orders:
		item_code = row.get("item_code")
		if order_count_map.get(item_code) is None:
			order_count_map[item_code] = 1
		else:
			order_count_map[item_code] += 1

	return order_count_map

def get_open_sales_orders_count_for_batche(variants_list, warehouse=None):
	filters=[
		["Sales Order", "docstatus", "=", 1],
		["Sales Order Item", "delivered_qty", "=", 0],
		["Sales Order Item", "item_code", "in", variants_list],
	]

	if warehouse:
		filters.append(["Sales Order Item", "warehouse", "=", warehouse])

	open_sales_orders = frappe.db.get_list(
		"Sales Order",
		fields=["name", "`tabSales Order Item`.item_code"],
		filters=filters,
		distinct=1,
	)

	order_count_map = {}
	for row in open_sales_orders:
		item_code = row.get("item_code")
		if order_count_map.get(item_code) is None:
			order_count_map[item_code] = 1
		else:
			order_count_map[item_code] += 1

	return order_count_map

def get_stock_details_map(variant_list, warehouse=None):
	filters={"item_code": ["in", variant_list]}

	if warehouse:
		filters["warehouse"] = warehouse
	
	stock_details = frappe.db.get_all(
		"Bin",
		fields=[
			"sum(planned_qty) as planned_qty",
			"sum(actual_qty) as actual_qty",
			"sum(projected_qty) as projected_qty",
			"item_code",
		],
		filters=filters,
		group_by="item_code",
	)

	stock_details_map = {}
	for row in stock_details:
		name = row.get("item_code")
		stock_details_map[name] = {
			"Inventory": row.get("actual_qty"),
			"In Production": row.get("planned_qty"),
		}

	return stock_details_map


def get_batch_details_map(variant_list, warehouse=None):
	batch_details = frappe.db.get_all(
		"Batch",
		fields=[
			"count(*) as total_batches",
			"item",
		],
		filters={
		    "item": ["in", variant_list],
		    "batch_qty": [">", 0]
        },
		group_by="item",
	)

	batch_details_map = {}
	for row in batch_details:
		name = row.get("item")
		batch_details_map[name] = {
			# "Item": row.get("item"),
			"Total": row.get("total_batches"),
		}

	return batch_details_map


def get_case_details_map(variant_list, warehouse=None):
	filters=[
		["Case Detail", "enabled", "=", True],
		["Case Detail", "contents", "=", "Short Length"],
		["Case Detail Item", "item_code", "in", variant_list],
	]

	if warehouse:
		filters.append(["Case Detail", "warehouse", "=", warehouse])

	case_details = frappe.db.get_list(
		"Case Detail",
		fields=["name", "`tabCase Detail Item`.item_code"],
		filters=filters,
		distinct=1,
	)

	item_count_map = {}
	for row in case_details:
		item_code = row.get("item_code")
		if item_count_map.get(item_code) is None:
			item_count_map[item_code] = 1
		else:
			item_count_map[item_code] += 1

	return item_count_map


def get_attribute_values_map(variant_list):
	attribute_list = frappe.db.get_all(
		"Item Variant Attribute",
		fields=["attribute", "attribute_value", "parent"],
		filters={"parent": ["in", variant_list]},
	)

	attr_val_map = {}
	for row in attribute_list:
		name = row.get("parent")
		if not attr_val_map.get(name):
			attr_val_map[name] = {}

		attr_val_map[name][row.get("attribute")] = row.get("attribute_value")

	return attr_val_map

