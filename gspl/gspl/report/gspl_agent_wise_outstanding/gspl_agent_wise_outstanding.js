frappe.query_reports["GSPL Agent Wise Outstanding"] = {
	"filters": [
		{
			"fieldname": "to_date",
			"label": __("Up To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},
		{
			"fieldname": "sales_partner",
			"label": __("Agent"),
			"fieldtype": "Link",
			"options": "Sales Partner"
		}
	]
};