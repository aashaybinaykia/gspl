// Copyright (c) 2024, GSPL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GSPL Total Cases"] = {
    "filters": [
        {
            "fieldname": "new_item_code",
            "label": __("Case Number"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "bundle_type",
            "label": __("Bundle Type"),
            "fieldtype": "Link",
            "options": "Item"
        },
        {
            "fieldname": "status",
            "label": __("Status"),
            "fieldtype": "Select",
            "options": "\nActive\nDisabled\nSold",
            "default": "Active"
        },
        {
            "fieldname": "contents",
            "label": __("Contents"),
            "fieldtype": "Select",
            "options": "\nThaan\nShort Length\nPiece\nCombi"
        },
        {
            "fieldname": "warehouse",
            "label": __("Warehouse"),
            "fieldtype": "Link",
            "options": "Warehouse"
        },
        {
            "fieldname": "rack",
            "label": __("Rack"),
            "fieldtype": "Data"
        },
        {
            "fieldname": "brand",
            "label": __("Brand"),
            "fieldtype": "Link",
            "options": "Brand"
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "enabled",
            "label": __("Enabled"),
            "fieldtype": "Check",
            "default": 1
        }
    ]
};