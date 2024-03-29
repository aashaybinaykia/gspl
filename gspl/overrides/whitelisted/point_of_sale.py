from __future__ import unicode_literals

import frappe


@frappe.whitelist()
def search_for_serial_or_batch_or_barcode_number(search_value):
    # search batch no
	batch_no_data = frappe.db.get_value(
		"Batch", search_value, ["name as batch_no", "item as item_code"], as_dict=True
	)
	if batch_no_data:
		return batch_no_data

	# search barcode no
	barcode_data = frappe.db.get_value(
		"Item Barcode", {"barcode": search_value}, ["barcode", "parent as item_code"], as_dict=True
	)
	if barcode_data:
		return barcode_data

	# search serial no
	serial_no_data = frappe.db.get_value(
		"Serial No", search_value, ["name as serial_no", "item_code"], as_dict=True
	)
	if serial_no_data:
		return serial_no_data

	return {}
