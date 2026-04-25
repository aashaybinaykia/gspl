// Copyright (c) 2025, GSPL and contributors
// For license information, please see license.txt

frappe.ui.form.on('Road Challan', {
    onload: function(frm) {
        // Filter 'From' and 'To' address to show only 'Is Your Company Address'
        frm.set_query("from", function() {
            return {
                filters: {
                    "is_your_company_address": 1
                }
            };
        });

        frm.set_query("to", function() {
            return {
                filters: {
                    "is_your_company_address": 1
                }
            };
        });

        // Filter Delivery Notes - Only last 90 days
        frm.fields_dict["delivery_notes"].grid.get_field("delivery_note").get_query = function() {
            return {
                filters: {
                    "creation": [">=", frappe.datetime.add_days(frappe.datetime.nowdate(), -90)]
                }
            };
        };

        // Filter Stock Entries - Only last 90 days
        frm.fields_dict["stock_entries"].grid.get_field("stock_entry").get_query = function() {
            return {
                filters: {
                    "creation": [">=", frappe.datetime.add_days(frappe.datetime.nowdate(), -90)]
                }
            };
        };

        // Filter Case Details - Only Active Cases
        frm.fields_dict["case_details"].grid.get_field("case_detail").get_query = function() {
            return {
                filters: {
                    "status": "Active"
                }
            };
        };
    }
});

