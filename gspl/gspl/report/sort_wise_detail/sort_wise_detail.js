// Copyright (c) 2026, GSPL
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sort Wise Detail"] = {
    "filters": [
        {
            "fieldname": "item",
            "label": __("Sort Number"),
            "fieldtype": "Link",
            "options": "Item",
            "reqd": 1,
            "get_query": function() {
                return {
                    filters: {
                        "has_variants": 1
                    }
                }
            }
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
        }
    ]
};