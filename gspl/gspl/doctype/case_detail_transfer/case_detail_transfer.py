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

		for row in self.items:
			case_detail = frappe.get_doc("Case Detail", row.case_detail)

			for item in case_detail.items:
				se.append('items', {
					'item_code': item.item_code,
					's_warehouse': row.source_warehouse,
					't_warehouse': row.target_warehouse,
					'qty': item.qty,
					'batch_no': item.batch_no,
				})

		se.case_detail_transfer = self.name
		se.save()
		se.submit()

		for row in self.items:
			self.update_case_detail_warehouse(row.case_detail, row.target_warehouse)

		self.stock_entry = se.name
		self.save()

	def cancel_stock_entry(self):
		se = frappe.get_doc("Stock Entry", self.stock_entry)
		se.cancel()

		for row in self.items:
			self.update_case_detail_warehouse(row.case_detail, row.source_warehouse)

	def update_case_detail_warehouse(self, case_detail, warehouse):
		frappe.db.set_value("Case Detail", case_detail, 'warehouse', warehouse)

