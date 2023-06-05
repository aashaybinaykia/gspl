# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import logger

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)


def execute(filters=None):
    columns = [
        {
            "fieldname": "template",
            "label": 'Template',
            "fieldtype": "Link",
            "options": "Item",
            "width": 200,
        },
        {
            'label': 'Group',
            'fieldname': 'group',
            'fieldtype': 'Data',
            'width': 100
        },
        {
            'label': 'Packed Assortment',
            'fieldname': 'packed_assortment',
            'fieldtype': 'Data',
            'width': 200
        },
        {
            'label': 'Loose Assortment',
            'fieldname': 'loose_assortment',
            'fieldtype': 'Data',
            'width': 200
        },
        {
            'label': 'Cash Rate',
            'fieldname': 'cash_rate',
            'fieldtype': 'Currency',
            'options': 'currency',
            'width': 100
        }
    ]

    data = get_template_data(filters)

    return columns, data


def get_template_data(filters):
    item_filters = {
        "has_variants": True,
    }
    if filters.get('brand'):
        item_filters['brand'] = filters.get('brand')

    item_templates = frappe.get_all("Item", fields=["*"], filters=item_filters)
    item_template_item_codes = list(map(lambda x: x.item_code, item_templates))
    item_variants = frappe.get_all('Item',
                                   filters={'variant_of': [
                                       "in", item_template_item_codes]},
                                   fields=['name', 'variant_of', 'attributes.attribute_value'],
                                   order_by='attribute_value asc')

    item_variant_names = list(map(lambda x: x.name, item_variants))
    variants_dict = {}
    for variant in item_variants:
        variants_dict.setdefault(variant.variant_of, []).append(variant)

    batches = frappe.get_all('Batch', filters={'batch_qty': ['>', 0], 'item': ['in', item_variant_names]}, fields=[
                             'name', 'item', 'batch_qty', 'disabled'])

    variant_batches_dict = {}
    for batch in batches:
        variant_batches_dict.setdefault(batch.item, {})
        variant_batches_dict[batch.item].setdefault('batch_qty', batch.batch_qty)
        variant_batches_dict[batch.item].setdefault('enabled_batches', [])
        variant_batches_dict[batch.item].setdefault('disabled_batches', [])

        if batch.disabled:
            variant_batches_dict[batch.item]['disabled_batches'].append(batch)
        else:
            variant_batches_dict[batch.item]['enabled_batches'].append(batch)

    item_prices = frappe.get_all(
        'Item Price', filters={'item_code': ["in", item_template_item_codes], 'price_list': 'Cash'}, fields=['item_code', 'price_list_rate'])

    item_prices_dict = {}
    for item_price in item_prices:
        item_prices_dict.setdefault(
            item_price.item_code, []).append(item_price)

    template_data = []

    logger.info("Total item templates: %s" % len(item_templates))
    logger.info("Total item_variants: %s" % len(item_variants))
    logger.info("Total batches: %s" % len(batches))
    logger.info("Total item_prices: %s" % len(item_prices))

    for item_template in item_templates:
        template = item_template.item_code
        variants = variants_dict.get(template, [])

        logger.info("Template: %s" % template)
        logger.info("Variants len: %s" % len(variants))

        packed_assortment_p = {}
        variant_batches_count_p = []
        packed_assortment_l = {}
        variant_batches_count_l = []
        batch_qty = 0

        for variant in variants:
            attribute_value = variant.attribute_value
            # batches = frappe.get_all('Batch', filters={'item': variant.name, 'batch_qty': [
            #                          '>', 0], 'disabled': 1}, fields=['name'])

            # variant_batches = list(filter(lambda batch: batch.item == variant.name, batches))
            # enabled_batches = list(filter(lambda batch: batch.disabled == 0, variant_batches))
            # disabled_batches = list(filter(lambda batch: batch.disabled == 1, variant_batches))
            variant_batches = variant_batches_dict.get(variant.name, None)
            if variant_batches is not None:
                batch_qty += variant_batches['batch_qty']
                enabled_batches = variant_batches['enabled_batches']
                disabled_batches = variant_batches['disabled_batches']
                enabled_batches_len = len(enabled_batches)
                disabled_batches_len = len(disabled_batches)

                if enabled_batches_len > 0:
                    # packed_assortment_l[attribute_value] = enabled_batches_len
                    variant_batches_count_l.append(
                        str(attribute_value) + ': ' + str(enabled_batches_len))
                if disabled_batches_len > 0:
                    variant_batches_count_p.append(
                        str(attribute_value) + ': ' + str(disabled_batches_len))
                # packed_assortment_p[attribute_value] = disabled_batches_len

        cash_rate = 0
        item_price = item_prices_dict.get(template, [])
        if len(item_price):
            cash_rate = item_price[0].price_list_rate

        if len(variant_batches_count_p) or len(variant_batches_count_l):
            template_data.append({
                'template': template,
                'group': item_template.item_group,
                'packed_assortment': ", ".join(variant_batches_count_p),
                'loose_assortment': ", ".join(variant_batches_count_l),
                'cash_rate': cash_rate,

                'batch_qty': batch_qty,
            })

    template_data = sorted(template_data, key=lambda x: x['batch_qty'], reverse=True)

    logger.info("End of get_template_data")

    return template_data
