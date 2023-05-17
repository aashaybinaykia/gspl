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
    # items = items = frappe.get_all("Item", fields=["*"], filters={"has_variants": True, "brand": 'Arvind'})
    items = items = frappe.get_all("Item", fields=["*"], filters=item_filters)

    template_data = []

    for item in items:



        template = item.item_code
        logger.debug(template)
        packed_assortment_p = get_template_packed_assortment(template)
        packed_assortment_l = get_template_loose_assortment(template)


        cash_rate = frappe.get_value('Item Price', {'item_code': template, 'price_list': 'Cash'}, 'price_list_rate')

        variant_batches_count_p= []
        for attribute_value in packed_assortment_p:
            count = packed_assortment_p[attribute_value]
            variant_batches_count_p.append(str(attribute_value) + ': ' + str(count))

        variant_batches_count_l= []
        for attribute_value in packed_assortment_l:
            count = packed_assortment_l[attribute_value]
            variant_batches_count_l.append(str(attribute_value) + ': ' + str(count))

        template_data.append({
            'template': template,
            'group': item.item_group,
            'packed_assortment': ", ".join(variant_batches_count_p),
            'loose_assortment': ", ".join(variant_batches_count_l),
            'cash_rate': cash_rate
        })

    return template_data


def get_template_packed_assortment(template):
    variants = frappe.get_all('Item',
                          filters={'variant_of': template},
                          fields=['name', 'attributes.attribute_value'])

    variant_batches_count = {}
    for variant in variants:
        attribute_values = variant.attribute_value
        batches = frappe.get_all('Batch', filters={'item': variant.name, 'batch_qty': ['>', 0], 'disabled': 1}, fields=['name'])
        
        if len(batches) > 0:
            count = len(batches)
            variant_batches_count[(attribute_values)] = count

    return variant_batches_count

def get_template_loose_assortment(template):
    variants = frappe.get_all('Item',
                          filters={'variant_of': template},
                          fields=['name', 'attributes.attribute_value'])

    variant_batches_count = {}
    for variant in variants:
        attribute_values = variant.attribute_value
        batches = frappe.get_all('Batch', filters={'item': variant.name, 'batch_qty': ['>', 0], 'disabled': 0}, fields=['name'])
        
        if len(batches) > 0:
            count = len(batches)
            variant_batches_count[(attribute_values)] = count

    return variant_batches_count




