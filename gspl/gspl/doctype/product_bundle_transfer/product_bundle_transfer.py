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

		se.product_bundle_transfer = self.name
		se.save()
		se.submit()

		for row in self.items:
			self.update_product_bundle_warehouse(row.product_bundle, row.target_warehouse)

		self.stock_entry = se.name
		self.save()

	def cancel_stock_entry(self):
		se = frappe.get_doc("Stock Entry", self.stock_entry)
		se.cancel()

		for row in self.items:
			self.update_product_bundle_warehouse(row.product_bundle, row.source_warehouse)

	def update_product_bundle_warehouse(self, product_bundle, warehouse):
		""" Updates Product Bundle warehouse """
		frappe.db.set_value("Product Bundle", product_bundle, 'warehouse', warehouse)
