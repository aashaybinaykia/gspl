
from __future__ import unicode_literals

import frappe
from frappe import _

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
