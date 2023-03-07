import copy
import json

import frappe
from frappe import _
from frappe.utils import cstr, flt
from erpnext.controllers.item_variant import *


class ItemVariantExistsError(frappe.ValidationError):
    pass


class InvalidItemAttributeValueError(frappe.ValidationError):
    pass


class ItemTemplateCannotHaveStock(frappe.ValidationError):
    pass


@frappe.whitelist()
def create_variant_override(item, args):
    if isinstance(args, str):
        args = json.loads(args)

    template = frappe.get_doc("Item", item)
    variant = frappe.new_doc("Item")
    variant.variant_based_on = "Item Attribute"
    variant_attributes = []

    for d in template.attributes:
        variant_attributes.append({"attribute": d.attribute, "attribute_value": args.get(d.attribute)})

    variant.set("attributes", variant_attributes)
    copy_attributes_to_variant(template, variant)
    make_variant_item_code_override(template.item_code, template.item_name, variant)

    return variant


def make_variant_item_code_override(template_item_code, template_item_name, variant):
    """Uses template's item code and abbreviations to make variant's item code"""
    if variant.item_code:
        return

    abbreviations_code = []
    abbreviations_name = []
    i = 0
    for attr in variant.attributes:
        item_attribute = frappe.db.sql(
            """select i.numeric_values, v.abbr
            from `tabItem Attribute` i left join `tabItem Attribute Value` v
                on (i.name=v.parent)
            where i.name=%(attribute)s and (v.attribute_value=%(attribute_value)s or i.numeric_values = 1)""",
            {"attribute": attr.attribute, "attribute_value": attr.attribute_value},
            as_dict=True,
        )

        if not item_attribute:
            continue
            # frappe.throw(_('Invalid attribute {0} {1}').format(frappe.bold(attr.attribute),
            # 	frappe.bold(attr.attribute_value)), title=_('Invalid Attribute'),
            # 	exc=InvalidItemAttributeValueError)

        abbr_or_value = (
            cstr(attr.attribute_value) if item_attribute[0].numeric_values else item_attribute[0].abbr
        )
        if attr.attribute == "Category" and i>0:
            abbreviations_code.append(abbr_or_value)
        else:
            abbreviations_code.append(abbr_or_value)
            abbreviations_name.append(abbr_or_value)
            
        i=i+1

    if abbreviations_code:
        variant.item_code = "{0}-{1}".format(template_item_code, "-".join(abbreviations_code))
        variant.item_name = "{0}-{1}".format(template_item_name, "-".join(abbreviations_name))


@frappe.whitelist()
def enqueue_multiple_variant_creation_override(item, args):
    # There can be innumerable attribute combinations, enqueue
    if isinstance(args, str):
        variants = json.loads(args)
    total_variants = 1
    for key in variants:
        total_variants *= len(variants[key])
    if total_variants >= 600:
        frappe.throw(_("Please do not create more than 500 items at a time"))
        return
    if total_variants < 10:
        return create_multiple_variants_override(item, args)
    else:
        frappe.enqueue(
            "gspl.overrides.whitelisted.item_variant.create_multiple_variants_override",
            item=item,
            args=args,
            now=frappe.flags.in_test,
        )
        return "queued"


def create_multiple_variants_override(item, args):
    count = 0
    if isinstance(args, str):
        args = json.loads(args)

    args_set = generate_keyed_value_combinations(args)

    for attribute_values in args_set:
        if not get_variant(item, args=attribute_values):
            variant = create_variant_override(item, attribute_values)
            variant.save()
            count += 1

    return count
    