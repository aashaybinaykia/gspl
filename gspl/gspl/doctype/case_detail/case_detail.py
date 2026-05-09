# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from collections import defaultdict
from frappe.utils import now_datetime

from erpnext.stock.doctype.batch.batch import get_batch_qty


class CaseDetail(Document):
	def validate(self):
		valid_disabled_warehouses = ["GD Shop - GSPL", "Infra Park - GSPL", "Shop - GSPL", "38, Armenian Street - GSPL"]
		pass
		# if (not self.enabled and (self.warehouse not in valid_disabled_warehouses)):
		# 	frappe.throw("Case can only open in company warehouse")

	def before_save(self):
		self.set_case_type_and_content()

		# ✅ ADDED: ensure same-batch, single-source, full-batch transfer into self.warehouse
		# and update row.qty to the full batch qty (your requirement)
		# if self.enabled:
		# 	auto_transfer_full_batch_from_single_source(self)

		self.enable_disable_batch()
		self.calculate_rate_and_qty()

	def set_case_type_and_content(self):
		item_templates = []
		has_template = False
		template_name = "mixed"	

		total_items_in_case = len(self.items)
		sl_items = 0

		for row in self.items:

			# Check SL eligibility
			qty = row.qty
			if ((qty>=3) & (qty<=8.5)):
				sl_items += 1

			item = frappe.get_doc("Item", row.item_code)

			if item.variant_of:
				if item.variant_of not in item_templates:
					item_templates.append(item.variant_of)
					has_template = True
			else:
				if row.item_code not in item_templates:
					item_templates.append(row.item_code)
					has_template = True

		if has_template and len(item_templates) == 1:
			template_name = item_templates[0]

		self.bundle_type = template_name

		bundle = frappe.get_doc("Item", item_templates[0])
		self.brand = bundle.brand
		self.item_group = bundle.item_group

		# Updates "Case Detail Item Template" table
		self.set('item_templates', [])

		for item_template in item_templates:
			self.append('item_templates', {
				'item_template': item_template,
			})

		#Setting Content Type
		sl_threshold = 0.7
		sample_item = frappe.get_doc("Item", self.items[0].item_code)
		sample_item_uom = sample_item.stock_uom
		content = self.uom_content_determiner(sample_item_uom)
		if content == 'NA':
			sl_perc = sl_items/total_items_in_case
			if sl_perc >= sl_threshold and self.enabled:
				content = 'Short Length'
			else:
				content = 'Thaan'

		self.contents = content

	def calculate_rate_and_qty(self):
		total_qty = sum([row.qty for row in self.items])
		total_amount = sum([row.qty * row.rate for row in self.items])

		self.total_qty = total_qty
		self.total_amount = total_amount

	def enable_disable_batch(self):
		if self.enabled:
			for row in self.items:
				if row.batch_no:
					batch_qty = get_batch_qty(batch_no=row.batch_no, warehouse=self.warehouse, item_code=row.item_code)
					if batch_qty != row.qty:
						frappe.throw(_(
							"Row #%s: Cannot enable Case Detail because Batch %s does not have enough stock." % (
								row.idx, row.batch_no,)))

					else:
						frappe.db.set_value("Batch", row.batch_no, 'disabled', True)
						frappe.db.set_value("Batch", row.batch_no, 'content', self.contents)

			frappe.db.set_value("Item", self.new_item_code, 'is_sales_item', True)
			self.status = "Active"

		else:
			for row in self.items:
				if row.batch_no:
					frappe.db.set_value("Batch", row.batch_no, 'disabled', False)
					frappe.db.set_value("Batch", row.batch_no, 'content', self.contents)
			
			# frappe.db.set_value("Item", self.new_item_code, 'is_sales_item', False)
			self.status = "Disabled"

	@staticmethod
	def uom_content_determiner(uom):
		if uom == 'Nos':
			return 'Combi'
		else:
			return 'NA'


# -----------------------------
# ADDED HELPERS (minimal, self-contained)
# -----------------------------
def auto_transfer_full_batch_from_single_source(doc):
	"""
	For each unique (item_code, batch_no) in doc.items:
	- If the batch is NOT present (>0) in doc.warehouse, pick ONE source warehouse with positive qty
	- Transfer the FULL batch qty from that single source into doc.warehouse
	- Update the row.qty to the FULL batch qty
	- Group all lines by (source -> target) so only one Stock Entry per pair
	"""
	if not getattr(doc, "items", None):
		return

	target_wh = (doc.get("warehouse") or "").strip()
	if not target_wh:
		# If your Case Detail always uses a single warehouse field on parent,
		# this must be set; otherwise you can change to per-row warehouses.
		return

	# Deduplicate by (item_code, batch_no) for this doc/warehouse
	wanted = {}  # (item, batch) -> a row reference (to write qty/uom if needed)
	for row in doc.items:
		item_code = (row.get("item_code") or "").strip()
		batch_no  = (row.get("batch_no") or "").strip()
		if not (item_code and batch_no):
			continue
		key = (item_code, batch_no)
		wanted[key] = row

	plan = defaultdict(list)  # (src_wh, target_wh) -> [lines]

	for (item_code, batch_no), row in wanted.items():
		# already present in target_wh?
		if _flt(get_batch_qty(batch_no=batch_no, warehouse=target_wh, item_code=item_code)) > 0:
			continue

		# find ONE source with positive qty for the exact batch
		src_wh, batch_qty = _find_single_source_with_full_batch(item_code, batch_no, exclude_warehouse=target_wh)
		if not src_wh:
			frappe.throw(f"Batch {batch_no} for item {item_code} not found in any warehouse to transfer into {target_wh}.")

		# update row qty to the FULL batch qty (your requirement)
		row.qty = batch_qty

		# choose uom: row.uom -> item stock_uom -> "Nos"
		uom = row.get("uom") or _get_stock_uom(item_code) or "Nos"

		plan[(src_wh, target_wh)].append({
			"item_code": item_code,
			"batch_no": batch_no,
			"qty": batch_qty,
			"uom": uom
		})

	# Create one Stock Entry per (src -> target)
	for (src_wh, tgt_wh), lines in plan.items():
		_create_and_submit_material_transfer(src_wh, tgt_wh, lines)


def _find_single_source_with_full_batch(item_code, batch_no, exclude_warehouse=None):
	"""
	Return (source_warehouse, batch_qty) from ONE warehouse holding this batch.
	Preference: highest qty, then latest posting.
	"""
	data = frappe.db.sql(
		"""
		SELECT
			sle.warehouse,
			SUM(sle.actual_qty) AS qty,
			MAX(CONCAT(sle.posting_date, ' ', IFNULL(sle.posting_time, '00:00:00'))) AS last_posting
		FROM `tabStock Ledger Entry` sle
		WHERE sle.item_code = %(item)s AND sle.batch_no = %(batch)s
		GROUP BY sle.warehouse
		HAVING qty > 0
		ORDER BY qty DESC, last_posting DESC
		""",
		{"item": item_code, "batch": batch_no},
		as_dict=True
	) or []

	for r in data:
		wh = r["warehouse"]
		if exclude_warehouse and wh == exclude_warehouse:
			continue
		qty = _flt(r["qty"])
		if qty > 0:
			return wh, qty

	return None, 0.0


def _create_and_submit_material_transfer(from_warehouse, to_warehouse, lines):
	"""
	lines: list of dicts {item_code, batch_no, qty, uom}
	Creates ONE Stock Entry per (source -> target), with one line per batch.
	"""
	if not lines:
		return

	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Transfer"
	se.from_warehouse = from_warehouse
	se.to_warehouse = to_warehouse
	se.set_posting_time = 1

	nowdt = now_datetime()
	se.posting_date = nowdt.date()
	se.posting_time = nowdt.time()

	for ln in lines:
		qty = _flt(ln["qty"])
		if qty <= 0:
			continue
		se.append("items", {
			"s_warehouse": from_warehouse,
			"t_warehouse": to_warehouse,
			"item_code": ln["item_code"],
			"batch_no": ln["batch_no"],
			"qty": qty,
			"uom": ln.get("uom") or _get_stock_uom(ln["item_code"]) or "Nos"
		})

	if not se.items:
		return

	se.flags.ignore_permissions = True
	se.insert()
	se.submit()


def _get_stock_uom(item_code):
	return frappe.db.get_value("Item", item_code, "stock_uom")


def _flt(v):
	try:
		return float(v or 0)
	except Exception:
		return 0.0
