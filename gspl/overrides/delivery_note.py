
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint

from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote


class CustomDeliveryNote(DeliveryNote):
    """
    Overrided DeliveryNote DocType
    """

    def validate_with_previous_doc(self):
        super(DeliveryNote, self).validate_with_previous_doc(
            {
                "Sales Order": {
                    "ref_dn_field": "against_sales_order",
                    "compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]],
                },
                "Sales Order Item": {
                    "ref_dn_field": "so_detail",
                    # "compare_fields": [["item_code", "="], ["uom", "="], ["conversion_factor", "="]],
                    "compare_fields": [["item_code", "="], ["uom", "="],],
                    "is_child_table": True,
                    "allow_duplicate_prev_row_id": True,
                },
                "Sales Invoice": {
                    "ref_dn_field": "against_sales_invoice",
                    "compare_fields": [["customer", "="], ["company", "="], ["project", "="], ["currency", "="]],
                },
                "Sales Invoice Item": {
                    "ref_dn_field": "si_detail",
                    "compare_fields": [["item_code", "="], ["uom", "="],],
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
                [
                    ["Sales Order", "against_sales_order", "so_detail"],
                    ["Sales Invoice", "against_sales_invoice", "si_detail"],
                ]
            )
