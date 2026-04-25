# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt


from operator import itemgetter
from typing import Any, Dict, List, Optional, TypedDict

import frappe
from frappe import _
from frappe.query_builder.functions import Coalesce, CombineDatetime
from frappe.utils import cint, date_diff, flt, getdate, logger
from frappe.utils.nestedset import get_descendants_of

import erpnext
from erpnext.stock.doctype.inventory_dimension.inventory_dimension import get_inventory_dimensions
from erpnext.stock.doctype.warehouse.warehouse import apply_warehouse_filter
from erpnext.stock.report.stock_ageing.stock_ageing import FIFOSlots, get_average_age
from erpnext.stock.utils import add_additional_uom_columns, is_reposting_item_valuation_in_progress


frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("gspl_reports", allow_site=True, file_count=10)


class GSPLPurchaseSaleFilter(TypedDict):
	brand: Optional[str]
	item_group: Optional[str]
	from_date: str
	to_date: str
	group_by: Optional[str]
	company: Optional[str]
	# item: Optional[str]
	# warehouse: Optional[str]
	# warehouse_type: Optional[str]
	# include_uom: Optional[str]  # include extra info in converted UOM
	# show_stock_ageing_data: bool
	# show_variant_attributes: bool


SLEntry = Dict[str, Any]


def execute(filters: Optional[GSPLPurchaseSaleFilter] = None):
	if not filters:
		filters = {}

	if filters.get("company"):
		company_currency = erpnext.get_company_currency(filters.get("company"))
	else:
		company_currency = frappe.db.get_single_value("Global Defaults", "default_currency")

	data = []
	columns = get_columns(filters)
	items = get_items(filters)

	logger.info("Columns: %s", columns)
	logger.info("Items len: %s", len(items))
	if not len(items):
		return columns, data

	sle = get_stock_ledger_entries(filters, items)

	# if no stock ledger entry found return
	logger.info("SLE len: %s", len(sle))
	if not sle:
		return columns, []

	iwb_map = get_item_warehouse_map(filters, sle)
	item_map = get_item_details(items, sle, filters)

	conversion_factors = {}

	_func = itemgetter(1)

	to_date = filters.get("to_date")

	logger.info("iwb_map len: %s", len(iwb_map))
	logger.info("item_map len: %s", len(item_map))
	# logger.info("iwb_map: %s", iwb_map)
	# logger.info("item_map: %s", item_map)

	for group_by_key in iwb_map:
		company = group_by_key[0]
		item = group_by_key[1]
		# warehouse = group_by_key[2]

		if item_map.get(item):
			qty_dict = iwb_map[group_by_key]

			report_data = {
				"currency": company_currency,
				"item_code": item,
				"company": company,
			}
			report_data.update(item_map[item])
			report_data.update(qty_dict)

			data.append(report_data)

	add_additional_uom_columns(columns, data, False, conversion_factors)
	logger.info(data)
	logger.info(columns)
	return columns, data

def get_columns(filters: GSPLPurchaseSaleFilter):
	columns = []

	if filters.get("group_by"):
		group_by = filters.get("group_by")
		group_by_column_map = {
			"Item": {
				"label": _("Item"),
				"fieldname": "item_code",
				"fieldtype": "Link",
				"options": "Item",
				"width": 150,
			},
			"Item Group": {
				"label": _("Item Group"),
				"fieldname": "item_group",
				"fieldtype": "Link",
				"options": "Item Group",
				"width": 150,
			},
			"Brand": {
				"label": _("Brand"),
				"fieldname": "brand",
				"fieldtype": "Link",
				"options": "Brand",
				"width": 150,
			},
			"Item Template": {
				"label": _("Item Template"),
				"fieldname": "variant_of",
				"fieldtype": "Link",
				"options": "Item",
				"width": 150,
			},

			
		}
		group_by_column = group_by_column_map.get(group_by)
		columns.append(group_by_column)

		# if group_by == "Item Group" and filters.get("brand"):
		# 	columns.append(group_by_column_map.get("Brand"))
		# elif group_by == "Brand" and filters.get("item_group"):
		# 	columns.append(group_by_column_map.get("Item Group"))

	columns.extend([
		{
			"label": _("Opening Qty"),
			"fieldname": "opening_qty",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty",
		},
		{
			"label": _("Opening Value"),
			"fieldname": "opening_val",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
		{
			"label": _("Purchase Qty"),
			"fieldname": "purchase_qty",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty",
		},
		{
			"label": _("Purchase Value"),
			"fieldname": "purchase_val",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
		{
			"label": _("Sale Qty"),
			"fieldname": "sale_qty",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty",
		},
		{
			"label": _("Sale Value"),
			"fieldname": "sale_val",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
		{
			"label": _("Balance Qty"),
			"fieldname": "bal_qty",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty",
		},
		{
			"label": _("Balance Value"),
			"fieldname": "bal_val",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
		{
			"label": _("Other Qty"),
			"fieldname": "other_qty",
			"fieldtype": "Float",
			"width": 120,
			"convertible": "qty",
		},
		{
			"label": _("Other Value"),
			"fieldname": "other_val",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
	])

	return columns


def apply_conditions(query, filters):
	sle = frappe.qb.DocType("Stock Ledger Entry")
	# warehouse_table = frappe.qb.DocType("Warehouse")

	if not filters.get("from_date"):
		frappe.throw(_("'From Date' is required"))

	if to_date := filters.get("to_date"):
		query = query.where(sle.posting_date <= to_date)
	else:
		frappe.throw(_("'To Date' is required"))

	if company := filters.get("company"):
		query = query.where(sle.company == company)

	# if filters.get("warehouse"):
	# 	query = apply_warehouse_filter(query, sle, filters)
	# elif warehouse_type := filters.get("warehouse_type"):
	# 	query = (
	# 		query.join(warehouse_table)
	# 		.on(warehouse_table.name == sle.warehouse)
	# 		.where(warehouse_table.warehouse_type == warehouse_type)
	# 	)

	return query


def get_stock_ledger_entries(filters: GSPLPurchaseSaleFilter, items: List[str]) -> List[SLEntry]:
	sle = frappe.qb.DocType("Stock Ledger Entry")
	item_table = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(sle)
		.inner_join(item_table)
		.on(sle.item_code == item_table.name)
		.select(
			sle.item_code,
			item_table.item_group,
			item_table.brand,
			item_table.variant_of,
			sle.warehouse,
			sle.posting_date,
			sle.actual_qty,
			sle.valuation_rate,
			sle.company,
			sle.voucher_type,
			sle.qty_after_transaction,
			sle.stock_value_difference,
			sle.item_code.as_("name"),
			sle.voucher_no,
			sle.stock_value,
			sle.batch_no,
		)
		.where((sle.docstatus < 2) & (sle.is_cancelled == 0) & (sle.voucher_type.isin(["Stock Reconciliation", "Sales Invoice", "Purchase Receipt", "Stock Entry", "Purchase Invoice", "Delivery Note"])))
		.orderby(CombineDatetime(sle.posting_date, sle.posting_time))
		.orderby(sle.creation)
		.orderby(sle.actual_qty)
	)

	# inventory_dimension_fields = get_inventory_dimension_fields()
	# if inventory_dimension_fields:
	# 	for fieldname in inventory_dimension_fields:
	# 		query = query.select(fieldname)
	# 		if fieldname in filters and filters.get(fieldname):
	# 			query = query.where(sle[fieldname].isin(filters.get(fieldname)))

	if items:
		query = query.where(sle.item_code.isin(items))

	query = apply_conditions(query, filters)
	return query.run(as_dict=True)


def get_opening_vouchers(to_date):
	opening_vouchers = {"Stock Entry": [], "Stock Reconciliation": []}

	se = frappe.qb.DocType("Stock Entry")
	sr = frappe.qb.DocType("Stock Reconciliation")

	vouchers_data = (
		frappe.qb.from_(
			(
				frappe.qb.from_(se)
				.select(se.name, Coalesce("Stock Entry").as_("voucher_type"))
				.where((se.docstatus == 1) & (se.posting_date <= to_date) & (se.is_opening == "Yes"))
			)
			+ (
				frappe.qb.from_(sr)
				.select(sr.name, Coalesce("Stock Reconciliation").as_("voucher_type"))
				.where((sr.docstatus == 1) & (sr.posting_date <= to_date) & (sr.purpose == "Opening Stock"))
			)
		).select("voucher_type", "name")
	).run(as_dict=True)

	if vouchers_data:
		for d in vouchers_data:
			opening_vouchers[d.voucher_type].append(d.name)

	return opening_vouchers


def get_item_warehouse_map(filters: GSPLPurchaseSaleFilter, sle: List[SLEntry]):
	iwb_map = {}
	from_date = getdate(filters.get("from_date"))
	to_date = getdate(filters.get("to_date"))
	opening_vouchers = get_opening_vouchers(to_date)
	float_precision = cint(frappe.db.get_default("float_precision")) or 3

	for d in sle:
		# logger.info("*" * 10)
		# logger.info(d.name)
		# logger.info(d.voucher_type)
		# logger.info(d.voucher_no)
		# template = get_item_template(d.item_code)
		group_by_key = get_group_by_key(d, filters)
		if group_by_key not in iwb_map:
			# logger.info("Group by key: ", group_by_key)
			iwb_map[group_by_key] = frappe._dict(
				{
					"opening_qty": 0.0,
					"opening_val": 0.0,
					"purchase_qty": 0.0,
					"purchase_val": 0.0,
					"sale_qty": 0.0,
					"sale_val": 0.0,
					"bal_qty": 0.0,
					"bal_val": 0.0,
					"other_qty": 0.0,
					"other_val": 0.0,

					# "in_qty": 0.0,
					# "in_val": 0.0,
					# "out_qty": 0.0,
					# "out_val": 0.0,
					# "val_rate": 0.0,
				}
			)

		qty_dict = iwb_map[group_by_key]
		# for field in inventory_dimensions:
		# 	qty_dict[field] = d.get(field)

		if d.voucher_type == "Stock Reconciliation" and not d.batch_no:
			qty_diff = flt(d.qty_after_transaction) - flt(qty_dict.bal_qty)
		else:
			qty_diff = flt(d.actual_qty)

		value_diff = flt(d.stock_value_difference)

		if d.posting_date < from_date or d.voucher_no in opening_vouchers.get(d.voucher_type, []):
			qty_dict.opening_qty += qty_diff
			qty_dict.opening_val += value_diff

			# if d.voucher_type == "Purchase Invoice":
			# 	# logger.info("Purchase Invoice actual qty: %s", flt(d.actual_qty))
			# 	qty_dict.purchase_qty += flt(d.actual_qty)

		elif d.posting_date >= from_date and d.posting_date <= to_date:

			if d.voucher_type == "Purchase Invoice" or d.voucher_type == "Purchase Receipt":
				# logger.info("Purchase Invoice actual qty: %s", flt(d.actual_qty))
				# qty_dict.purchase_qty += flt(d.actual_qty)
				qty_dict.purchase_qty += qty_diff
				qty_dict.purchase_val += value_diff

			# else:
			# 	# qty_dict.out_qty += abs(qty_diff)
			# 	# qty_dict.out_val += abs(value_diff)
			# 	# qty_dict.sale_qty += abs(qty_diff)
			# 	# qty_dict.sale_val += abs(value_diff)

			# 	if d.voucher_type == "Stock Entry":
			# 		stock_entry_type = frappe.get_value(d.voucher_type, d.voucher_no, 'stock_entry_type')
			# 		if stock_entry_type == "Material Receipt":
			# 			qty_dict.sale_qty += abs(flt(d.actual_qty))
			# 			# qty_dict.sale_qty += abs(qty_diff)
			# 			qty_dict.sale_val += abs(value_diff)

			elif d.voucher_type == "Delivery Note" or d.voucher_type == "Sales Invoice":
				qty_dict.sale_qty -= flt(d.actual_qty)
					# qty_dict.sale_qty += abs(qty_diff)
				qty_dict.sale_val -= value_diff

			else:
				qty_dict.other_qty += qty_diff
				qty_dict.other_val += value_diff
				

		# qty_dict.val_rate = d.valuation_rate
		qty_dict.bal_qty += qty_diff
		qty_dict.bal_val += value_diff
		# qty_dict.bal_qty += qty_dict.opening_qty + qty_dict.purchase_qty - qty_dict.sale_qty
		# qty_dict.bal_val += qty_dict.opening_val + qty_dict.purchase_val - qty_dict.sale_val

	# logger.info("iwb_map before filters: %s", iwb_map)

	iwb_map = filter_items_with_no_transactions(iwb_map, float_precision)

	return iwb_map

def get_item_template(item_code,filters):
    # Get the item document for the provided item_code

    # Check if the item has a variant_of value
    if filters.get("group_by") == "Item Template":
        # Retrieve the item_name of the variant_of item
        item_template = frappe.get_value("Item", item_code, "item_name")
        return item_template
    else:
        # If there is no variant_of, consider the item itself as the template
        return item_code

def get_group_by_key(row, filters) -> tuple:
	group_by_key_map = {
		"Item": (row.company, row.item_code),
		"Item Group": (row.company, row.item_group),
		"Brand": (row.company, row.brand),
		"Item Template": (row.company,row.variant_of)
	    # "Item Template": (row.company, t),

	}
	logger.info("Group by key map: %s", group_by_key_map)
	logger.info("Group by filter value: %s", filters.get('group_by'))
	group_by_key = group_by_key_map.get(filters.get('group_by'), "Item")
	# group_by_key = {
	# 	"Item": (row.company, row.item_code),
	# 	"Item Group": (row.company, row.item_group),
	# 	"Brand": (row.company, row.brand),
	# }.get(filters.get('group_by'), "Item")
	logger.info("Group by key map: %s", group_by_key_map)
	logger.info("Group by key: %s", group_by_key)
	return tuple(group_by_key)


def filter_items_with_no_transactions(iwb_map, float_precision: float):
	pop_keys = []
	for group_by_key in iwb_map:
		qty_dict = iwb_map[group_by_key]

		no_transactions = True
		for key, val in qty_dict.items():
			# if key in inventory_dimensions:
			# 	continue

			val = flt(val, float_precision)
			qty_dict[key] = val
			if key != "val_rate" and val:
				no_transactions = False

		if no_transactions:
			pop_keys.append(group_by_key)

	for key in pop_keys:
		iwb_map.pop(key)

	return iwb_map


def get_items(filters: GSPLPurchaseSaleFilter) -> List[str]:
	"Get items based on item code, item group or brand."
	# if item_code := filters.get("item_code"):
	# 	return [item_code]
	# else:
	item_filters = {}
	if item_group := filters.get("item_group"):
		children = get_descendants_of("Item Group", item_group, ignore_permissions=True)
		item_filters["item_group"] = ("in", children + [item_group])
	if brand := filters.get("brand"):
		item_filters["brand"] = brand

	return frappe.get_all("Item", filters=item_filters, pluck="name", order_by=None)


def get_item_details(items: List[str], sle: List[SLEntry], filters: GSPLPurchaseSaleFilter):
	item_details = {}
	if not items:
		items = list(set(d.item_code for d in sle))

	if not items:
		return item_details

	item_table = frappe.qb.DocType("Item")

	query = (
		frappe.qb.from_(item_table)
		.select(
			item_table.name,
			item_table.item_name,
			item_table.description,
			item_table.item_group,
			item_table.variant_of,
			item_table.brand,
			item_table.stock_uom,
		)
		.where(item_table.name.isin(items))
	)

	# if uom := filters.get("include_uom"):
	# 	uom_conv_detail = frappe.qb.DocType("UOM Conversion Detail")
	# 	query = (
	# 		query.left_join(uom_conv_detail)
	# 		.on((uom_conv_detail.parent == item_table.name) & (uom_conv_detail.uom == uom))
	# 		.select(uom_conv_detail.conversion_factor)
	# 	)

	result = query.run(as_dict=1)

	for item_result in result:
		item_details_key = {
			"Item": item_result.name,
			"Item Group": item_result.item_group,
			"Item Template": item_result.variant_of,
			"Brand": item_result.brand,
		}.get(filters.get("group_by"), "Item")

		item_details.setdefault(item_details_key, item_result)

	# if filters.get("show_variant_attributes"):
	# 	variant_values = get_variant_values_for(list(item_details))
	# 	item_details = {k: v.update(variant_values.get(k, {})) for k, v in item_details.items()}

	return item_details
