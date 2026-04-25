# Copyright (c) 2024, GSPL and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, TypedDict

import frappe
from frappe import _
from frappe.utils import getdate



class GSPLSalesPartnerWisePaymentReceivedFilter(TypedDict):
	customer: Optional[str]
	sales_partner: Optional[str]
	from_date: str
	to_date: str
	group_by: Optional[str]


def execute(filters: Optional[GSPLSalesPartnerWisePaymentReceivedFilter] = None):
	if not filters:
		filters = {}

	# columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	
	return columns, data


def get_columns(filters: GSPLSalesPartnerWisePaymentReceivedFilter):
	columns = []

	if filters.get("group_by") == "Customer":
		columns.append({
			"label": _("Customer"),
			"fieldname": "customer",
			"fieldtype": "Link",
			"options": "Customer",
			"width": 150,
		})

	columns.extend([
		{
			"label": _("Sales Partner"),
			"fieldname": "sales_partner",
			"fieldtype": "Link",
			"options": "Sales Partner",
			"width": 150,
		},
		{
			"label": _("Total Amount Received"),
			"fieldname": "total_amount_received",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
	])

	return columns


def get_data(filters: GSPLSalesPartnerWisePaymentReceivedFilter) -> List[Dict[str, Any]]:

    customer_filter = filters.get("customer")
    sales_partner_filter = filters.get("sales_partner")

    if filters.get("group_by") == "Customer":
        query = """
            SELECT
                p.party AS customer,
                c.default_sales_partner AS sales_partner,
                SUM(CASE WHEN p.payment_type = 'Receive' THEN p.paid_amount ELSE 0 END) -
                SUM(CASE WHEN p.payment_type = 'Pay' THEN p.paid_amount ELSE 0 END) AS total_amount_received
            FROM
                `tabPayment Entry` p
            LEFT JOIN
                `tabCustomer` c ON p.party = c.name
            WHERE
                p.docstatus = 1
                AND (p.party = %(customer)s OR %(customer)s IS NULL)
                AND (c.default_sales_partner = %(sales_partner)s OR %(sales_partner)s IS NULL)
                AND p.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND c.name IS NOT NULL  -- Ensures only customers are included
            GROUP BY
                p.party
        """
    else:
        query = """
            SELECT
                sp.name AS sales_partner,
                SUM(CASE WHEN p.payment_type = 'Receive' THEN p.paid_amount ELSE 0 END) -
                SUM(CASE WHEN p.payment_type = 'Pay' THEN p.paid_amount ELSE 0 END) AS total_amount_received
            FROM
                `tabPayment Entry` p
            LEFT JOIN
                `tabCustomer` c ON p.party = c.name
            INNER JOIN
                `tabSales Partner` sp ON c.default_sales_partner = sp.name
            WHERE
                p.docstatus = 1
				AND (c.name = %(customer)s OR %(customer)s IS NULL)
                AND (c.default_sales_partner = %(sales_partner)s OR %(sales_partner)s IS NULL)
                AND p.posting_date BETWEEN %(from_date)s AND %(to_date)s
                AND c.name IS NOT NULL  -- Ensures only customers are included
            GROUP BY
                sp.name
        """

    data = frappe.db.sql(query, {
        "customer": customer_filter,
        "sales_partner": sales_partner_filter,
        "from_date": filters["from_date"],
        "to_date": filters["to_date"]
    }, as_dict=True)

    return data
