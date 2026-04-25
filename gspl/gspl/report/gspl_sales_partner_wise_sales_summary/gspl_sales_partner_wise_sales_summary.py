# Copyright (c) 2024, GSPL and contributors
# For license information, please see license.txt

from typing import Any, Dict, List, Optional, TypedDict

import frappe
from frappe import _
from frappe.utils import getdate



class GSPLSalesPartnerWiseSalesSummaryFilter(TypedDict):
	customer: Optional[str]
	sales_partner: Optional[str]
	from_date: str
	to_date: str
	group_by: Optional[str]


def execute(filters: Optional[GSPLSalesPartnerWiseSalesSummaryFilter] = None):
	if not filters:
		filters = {}

	# columns, data = [], []
	columns = get_columns(filters)
	data = get_data(filters)
	
	return columns, data


def get_columns(filters: GSPLSalesPartnerWiseSalesSummaryFilter):
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
			"label": _("Brand"),
			"fieldname": "brand",
			"fieldtype": "Link",
			"options": "Brand",
			"width": 150,
		},
		{
			"label": _("Price List"),
			"fieldname": "price_list",
			"fieldtype": "Link",
			"options": "Price List",
			"width": 150,
		},
		{
			"label": _("Total Amount"),
			"fieldname": "total_amount",
			"fieldtype": "Currency",
			"width": 120,
			"options": "currency",
		},
	])

	return columns

def get_data(filters: GSPLSalesPartnerWiseSalesSummaryFilter) -> List[Dict[str, Any]]:

    if filters.get("group_by") == "Customer":
        query = """
            SELECT
                si.customer AS customer,
				si.additional_discount_percentage AS disc,
                si.sales_partner AS sales_partner,
                sii.brand AS brand,
                sii.price_list AS price_list,
                SUM(sii.amount * (1 - si.additional_discount_percentage / 100)) AS total_amount
            FROM
                `tabSales Invoice` si
            INNER JOIN
                `tabSales Invoice Item` sii ON si.name = sii.parent
            WHERE
                si.docstatus = 1
                AND (si.customer = %(customer)s OR %(customer)s IS NULL)
                AND (si.sales_partner = %(sales_partner)s OR %(sales_partner)s IS NULL)
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY
                si.customer, si.sales_partner, sii.brand, sii.price_list
        """
    elif filters.get("group_by") == "Sales Partner":
        query = """
            SELECT
                si.sales_partner AS sales_partner,
                sii.brand AS brand,
                sii.price_list AS price_list,
                SUM(sii.amount) AS total_amount
            FROM
                `tabSales Invoice` si
            INNER JOIN
                `tabSales Invoice Item` sii ON si.name = sii.parent
            WHERE
                si.docstatus = 1
				AND (si.customer = %(customer)s OR %(customer)s IS NULL)
                AND (si.sales_partner = %(sales_partner)s OR %(sales_partner)s IS NULL)
                AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            GROUP BY
                si.sales_partner, sii.brand, sii.price_list
        """
    else:
        # Return an empty list for other cases
        return []

    data = frappe.db.sql(query, {
        "customer": filters.get("customer"),
        "sales_partner": filters.get("sales_partner"),
        "from_date": filters["from_date"],
        "to_date": filters["to_date"]
    }, as_dict=True)

    return data
