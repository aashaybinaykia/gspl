frappe.query_reports["GSPL Sales and Payment Summary"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "customer",
			"label": "Customer",
			"fieldtype": "Link",
			"options": "Customer"
		},
		{
			"fieldname": "sales_partner",
			"label": "Sales Partner",
			"fieldtype": "Link",
			"options": "Sales Partner"
		},
		{
			"fieldname": "customer_group",
			"label": "Customer Group",
			"fieldtype": "Link",
			"options": "Customer Group"
		},
		{
			"fieldname": "territory",
			"label": "Territory",
			"fieldtype": "Link",
			"options": "Territory"
		},
		{
			"fieldname": "sales_manager",
			"label": "Sales Manager",
			"fieldtype": "Link",
			"options": "Sales Person"
		},
		{
			"fieldname": "customer_grade",
			"label": "Customer Grade",
			"fieldtype": "Select",
			"options": "\nA\nOthers"
		}
	]
};
