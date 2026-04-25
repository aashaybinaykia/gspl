// File: gspl_consolidated_stock_ageing.js

frappe.query_reports["GSPL Consolidated Stock Ageing"] = {
    "filters": [
        {
            "fieldname": "company",
            "label": __("Company"),
            "fieldtype": "Link",
            "options": "Company",
            "default": frappe.defaults.get_user_default("Company"),
            "reqd": 1
        },
        {
            "fieldname": "ask_on_date",
            "label": __("As On Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group"
        },
        {
            "fieldname": "brand",
            "label": __("Brand"),
            "fieldtype": "Link",
            "options": "Brand"
        },
        {
            "fieldname": "range_1",
            "label": __("Ageing Range 1 (Days)"),
            "fieldtype": "Int",
            "default": 30
        },
        {
            "fieldname": "range_2",
            "label": __("Ageing Range 2 (Days)"),
            "fieldtype": "Int",
            "default": 60
        },
        {
            "fieldname": "range_3",
            "label": __("Ageing Range 3 (Days)"),
            "fieldtype": "Int",
            "default": 90
        }
    ],
	"prepared_report": 1
};