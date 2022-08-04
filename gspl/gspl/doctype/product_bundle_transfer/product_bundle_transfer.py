# Copyright (c) 2022, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ProductBundleTransfer(Document):
	
	def on_submit(self):
		self.create_stock_entry()

	def on_cancel(self):
		self.cancel_stock_entry()

	def create_stock_entry(self):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.posting_date = self.posting_date
		se.posting_time = self.posting_time

		for row in self.items:
			product_bundle = frappe.get_doc("Product Bundle", row.product_bundle)

			for item in product_bundle.items:
				se.append('items', {
					'item_code': item.item_code,
					's_warehouse': row.source_warehouse,
					't_warehouse': row.target_warehouse,
					'qty': item.qty,
					'batch_no': item.batch_no,
				})

			product_bundle.warehouse = row.target_warehouse
			product_bundle.save()

		se.save()
		se.submit()

		self.stock_entry = se.name
		self.save()


	def cancel_stock_entry(self):
		se = frappe.get_doc("Stock Entry", self.stock_entry)
		se.cancel()

		for row in self.items:
			frappe.db.set_value("Product Bundle", row.product_bundle, 'warehouse', row.source_warehouse)
