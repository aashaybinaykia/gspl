# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from erpnext.stock.doctype.batch.batch import get_batch_qty


class CaseDetail(Document):
	def validate(self):
		valid_disabled_warehouses = ["GD Shop - GSPL", "Infra Park - GSPL", "Shop - GSPL", "38, Armenian Street - GSPL"]
		pass
		# if (not self.enabled and (self.warehouse not in valid_disabled_warehouses)):
		# 	frappe.throw("Case can only open in company warehouse")

	def before_save(self):
		self.set_case_type_and_content()
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
					
					# Strict Warehouse & Quantity Check
					if batch_qty != row.qty:
						frappe.throw(_(
							"Row #{0}: Cannot enable Case Detail. Batch {1} must be physically present in warehouse '{2}' with exactly {3} qty."
						).format(row.idx, row.batch_no, self.warehouse, row.qty))
					else:
						frappe.db.set_value("Batch", row.batch_no, 'custom_locked_by_case_detail', 1)
						frappe.db.set_value("Batch", row.batch_no, 'content', self.contents)

			frappe.db.set_value("Item", self.new_item_code, 'is_sales_item', True)
			self.status = "Active"

		else:
			for row in self.items:
				if row.batch_no:
					frappe.db.set_value("Batch", row.batch_no, 'custom_locked_by_case_detail', 0)
					frappe.db.set_value("Batch", row.batch_no, 'content', self.contents)
			
			self.status = "Disabled"

	@staticmethod
	def uom_content_determiner(uom):
		if uom == 'Nos':
			return 'Combi'
		else:
			return 'NA'