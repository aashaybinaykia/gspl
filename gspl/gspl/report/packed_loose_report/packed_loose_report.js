// Copyright (c) 2023, GSPL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Packed Loose Report"] = {
	"filters": [
		{
			"fieldname": "brand",
			"label": __("Brand"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Brand",
		},
		
		{
			"fieldname": "group",
			"label": __("Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group",
		},
		{
			"fieldname": "content",
			"label": __("Content"),
			"fieldtype": "Select",
			"width": "80",
			"options": "\nThaan\nShort Length\nPiece\nCombi",
		},
		{
			"fieldname": "min_qty",
			"label": __("Minimum Quantity"),
			"fieldtype": "Float",
			"width": "80",
		},
		{
			"fieldname": "max_qty",
			"label": __("Maximum Quantity"),
			"fieldtype": "Float",
			"width": "80",
		},
	]
};
