# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class CaseDetailTransfer(Document):
	
	def on_submit(self):
		self.create_stock_entry()

	def on_cancel(self):
		self.cancel_stock_entry()

	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.set_posting_time = 1
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time

		# 1. Collect batches to toggle
		batches_to_toggle = []

		for row in self.items:
			case_detail = frappe.get_doc("Case Detail", row.case_detail)

			for item in case_detail.items:
				if item.batch_no:
					batches_to_toggle.append(item.batch_no)

				se.append('items', {
					'item_code': item.item_code,
					's_warehouse': row.source_warehouse,
					't_warehouse': row.target_warehouse,
					'qty': item.qty,
					'uom': item.uom, 
					'conversion_factor': item.get("conversion_factor") or 1.0, 
					'batch_no': item.batch_no,
					'use_serial_batch_fields': 1 
				})

		se.case_detail_transfer = self.name
		
		# Calculates transfer_qty and fetches UOMs before saving
		se.set_missing_values()
		
		# Remove duplicate batch numbers from our list
		batches_to_toggle = list(set(batches_to_toggle))

		# 2. Enable the batches
		for batch in batches_to_toggle:
			frappe.db.set_value("Batch", batch, "disabled", 0)

		# 3. Attempt to save and submit the Stock Entry
		try:
			se.save()
			se.submit()

			for row in self.items:
				self.update_case_detail_warehouse(row.case_detail, row.target_warehouse)

			self.stock_entry = se.name
			self.save()

		# 4. ALWAYS disable the batches afterward, even if the submit fails
		finally:
			for batch in batches_to_toggle:
				frappe.db.set_value("Batch", batch, "disabled", 1)


	def cancel_stock_entry(self):
		se = frappe.get_doc("Stock Entry", self.stock_entry)
		se.cancel()

		for row in self.items:
			self.update_case_detail_warehouse(row.case_detail, row.source_warehouse)

	def update_case_detail_warehouse(self, case_detail, warehouse):
		frappe.db.set_value("Case Detail", case_detail, 'warehouse', warehouse)