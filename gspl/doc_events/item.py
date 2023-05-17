
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def before_validate(doc, method):
    validate_item_variant_for_meters_uom(doc)    
    if doc.is_new():
        set_default_item_attributes(doc)


def validate_item_variant_for_meters_uom(doc):
    if doc.stock_uom == 'Meter':
        if not doc.has_variants and not doc.variant_of:
            frappe.throw(_("Either has_variants should be true, or variant_of should be set, if stock_uom is 'Meters'"))
    else:
        if doc.has_variants:
            frappe.throw(_("has_variants should be false, if stock_uom is not 'Meters'"))


def set_default_item_attributes(doc):
    """
    Set default Item Attribute to "Category" and "Shade" for New Item Template
    """

    if doc.is_new() and doc.has_variants and doc.variant_based_on == "Item Attribute":
        item_attributes = list(map(lambda d: d.attribute, doc.attributes))

        attributes_to_add = ["Shade"]
        for attribute in attributes_to_add:
            if frappe.db.exists("Item Attribute", attribute):
                if attribute not in item_attributes:
                    doc.append("attributes", {
                        "attribute": attribute
                    })
