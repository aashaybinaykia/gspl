// Copyright (c) 2024, GSPL and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["GSPL Interest Calculation"] = {
    "filters": [
        {
            "fieldname": "account",
            "label": __("Account"),
            "fieldtype": "Link",
            "options": "Account",
            "reqd": 1
        },
        {
            "fieldname": "fiscal_year",
            "label": __("Fiscal Year"),
            "fieldtype": "Link",
            "options": "Fiscal Year",
            "reqd": 1
        }
    ]
};
