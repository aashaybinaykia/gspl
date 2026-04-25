frappe.query_reports["GSPL Item Wise Sales Summary"] = {
    "filters": [
        {
            "fieldname": "sales_order",
            "label": __("Sales Order"),
            "fieldtype": "Link",
            "options": "Sales Order",
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_start()
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.month_end()
        },
        {
            "fieldname": "item",
            "label": __("Item"),
            "fieldtype": "Link",
            "options": "Item",
        },
        {
            "fieldname": "item_group",
            "label": __("Item Group"),
            "fieldtype": "Link",
            "options": "Item Group",
        },
        {
            "fieldname": "brand",
            "label": __("Brand"),
            "fieldtype": "Link",
            "options": "Brand",
        },
        {
            "fieldname": "content",
            "label": __("Content"),
            "fieldtype": "Select",
            "options": ["Loose", "Packed"]
        },
        {
            "fieldname": "view",
            "label": __("View"),
            "fieldtype": "Select",
            "options": ["Item-wise", "SO-wise","SO-wise-grouped"]
        }
    ]
};
