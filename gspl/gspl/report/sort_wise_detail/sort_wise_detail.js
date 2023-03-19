// Copyright (c) 2023, GSPL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sort Wise Detail"] = {
	"filters": [
		{
			reqd: 1,
			default: "",
			options: "Item",
			label: __("Item"),
			fieldname: "item",
			fieldtype: "Link",
			// get_query: () => {
			// 	return {
			// 		filters: { "has_variants": 1 }
			// 	}
			// }
		},
		{
			options: "Warehouse",
			label: __("Warehouse"),
			fieldname: "warehouse",
			fieldtype: "Link",
		},
	]
};
