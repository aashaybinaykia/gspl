
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint

from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
    """
    Overrided SalesInvoice DocType
    """

    def update_packing_list(self):
        super().update_packing_list()

        # Get batch from Product Bundle and update in the Packing List Item
        for packed_item in self.packed_items:
            product_bundle_item = frappe.get_doc("Product Bundle Item", {'parent': packed_item.parent_item, 'item_code': packed_item.item_code})
            packed_item.batch_no = product_bundle_item.batch_no

    def validate_with_previous_doc(self):
        super(SalesInvoice, self).validate_with_previous_doc(
            {
                "Sales Order": {
                    "ref_dn_field": "sales_order",
                    "compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]],
                },
                "Sales Order Item": {
                    "ref_dn_field": "so_detail",
                    # "compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
                    "compare_fields": [["item_code", "="], ["uom", "="]],
                    "is_child_table": True,
                    "allow_duplicate_prev_row_id": True,
                },
                "Delivery Note": {
                    "ref_dn_field": "delivery_note",
                    "compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]],
                },
                "Delivery Note Item": {
                    "ref_dn_field": "dn_detail",
                    "compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
                    "is_child_table": True,
                    "allow_duplicate_prev_row_id": True,
                },
            }
        )

        if (
            cint(frappe.db.get_single_value("Selling Settings", "maintain_same_sales_rate"))
            and not self.is_return
        ):
            self.validate_rate_with_reference_doc(
                [["Sales Order", "sales_order", "so_detail"], ["Delivery Note", "delivery_note", "dn_detail"]]
            )
