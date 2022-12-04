
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def before_validate(doc, method):
    if doc.is_new():
        set_default_item_attributes(doc)

def set_default_item_attributes(doc):
    """
    Set default Item Attribute to "Category" and "Shade" for New Item Template
    """

    if doc.is_new() and doc.has_variants and doc.variant_based_on == "Item Attribute":
        if frappe.db.exists("Item Attribute", "Category"):
            doc.append("attributes", {
                "attribute": "Category"
            })

        if frappe.db.exists("Item Attribute", "Shade"):
            doc.append("attributes", {
                "attribute": "Shade"
            })
