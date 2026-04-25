# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import logger

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=5000)


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
            'label': 'Item Name',
            'fieldname': 'item_name',
            'fieldtype': 'Data',
            'width': 200
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
            'label': 'Total Batches',
            'fieldname': 'total_batches',
            'fieldtype': 'Int',
            'width': 100
        },
                {
            'label': 'Total Qty',
            'fieldname': 'total_qty',
            'fieldtype': 'Float',
            'width': 100
        },
        {
            'label': 'Cash Rate',
            'fieldname': 'cash_rate',
            'fieldtype': 'Currency',
            'options': 'currency',
            'width': 100
        },
        {
            'label': 'SN Rate',
            'fieldname': 'sn_rate',
            'fieldtype': 'Currency',
            'options': 'currency',
            'width': 100
        },
        {
            'label': 'No Less Rate',
            'fieldname': 'no_less_rate',
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

    
    if filters.get('group'):
        item_filters['item_group'] = filters.get('group')

    item_templates = frappe.get_all("Item", fields=["*"], filters=item_filters)
    item_template_item_codes = list(map(lambda x: x.item_code, item_templates))
    item_variants = frappe.get_all('Item',
                                   filters={'variant_of': [
                                       "in", item_template_item_codes]},
                                   fields=['name', 'variant_of', 'attributes.attribute_value'],
                                   order_by='attribute_value asc')
    
    item_without_filters = {
        "has_variants": False,
        "variant_of": ''

    }
    
    if filters.get('brand'):
        item_without_filters['brand'] = filters.get('brand')

    
    if filters.get('group'):
        item_without_filters['item_group'] = filters.get('group')

    
    
    item_without_template = frappe.get_all('Item',
                                        filters=item_without_filters,
                                        fields=['name'])
    
    item_template_item_codes += list(map(lambda x: x.item_code, item_without_template))
    
    for item in item_without_template:
        item['variant_of'] = item['name']
        item['item_code'] = item['name']
        item['attribute_value'] = 'NA'

    
    item_variants += item_without_template
    item_template_item_codes += list(map(lambda x: x.item_code, item_without_template))

    # logger.info("Item Without Templates: %s" % item_without_template)
    # logger.info("Item item_variants Templates: %s" % item_variants)

    item_variant_names = list(map(lambda x: x.name, item_variants))

    # Set default values for min_qty and max_qty
    min_qty = 0
    max_qty = 10000

    # Update min_qty if provided in filters
    if filters.get('min_qty'):
        min_qty = filters.get('min_qty')

    # Update max_qty if provided in filters and greater than min_qty
    if filters.get('max_qty') and filters.get('max_qty') > 0:
        max_qty = filters.get('max_qty')

    # Construct the SQL query
    query = """
        SELECT
            name, item, batch_qty, disabled
        FROM
            `tabBatch`
        WHERE
            batch_qty > %(min_qty)s
            AND batch_qty < %(max_qty)s
    """

    # Add content filter if it exists
    if filters.get('content'):
        query += " AND content = %(content)s"

    # Execute the SQL query
    batches = frappe.db.sql(query, {
        "min_qty": min_qty,
        "max_qty": max_qty,
        "content": filters.get('content')
    }, as_dict=True)



    variants_dict = {}
    for variant in item_variants:
        variants_dict.setdefault(variant.variant_of, []).append(variant)

    variant_batches_dict = {}
    for batch in batches:
        variant_batches_dict.setdefault(batch.item, {})
        variant_batches_dict[batch.item].setdefault('batch_qty', batch.batch_qty)
        variant_batches_dict[batch.item].setdefault('total_qty', 0.0)
        variant_batches_dict[batch.item].setdefault('enabled_batches', [])
        variant_batches_dict[batch.item].setdefault('disabled_batches', [])

        variant_batches_dict[batch.item]['total_qty'] += batch.batch_qty

        if batch.disabled:
            variant_batches_dict[batch.item]['disabled_batches'].append(batch)
        else:
            variant_batches_dict[batch.item]['enabled_batches'].append(batch)

    item_prices_cash = frappe.get_all(
        'Item Price', filters={'item_code': ["in", item_template_item_codes], 'price_list': 'Cash'}, fields=['item_code', 'price_list_rate'], order_by='valid_from desc')

    item_prices_dict_cash = {}
    for item_price in item_prices_cash:
        item_prices_dict_cash.setdefault(
            item_price.item_code, []).append(item_price)



    item_prices_sn = frappe.get_all(
        'Item Price', filters={'item_code': ["in", item_template_item_codes], 'price_list': 'Super Net'}, fields=['item_code', 'price_list_rate'], order_by='valid_from desc')

    item_prices_dict_sn = {}
    for item_price in item_prices_sn:
        item_prices_dict_sn.setdefault(
            item_price.item_code, []).append(item_price)


    item_prices_nl = frappe.get_all(
        'Item Price', filters={'item_code': ["in", item_template_item_codes], 'price_list': 'No Less'}, fields=['item_code', 'price_list_rate'], order_by='valid_from desc')

    item_prices_dict_nl = {}
    for item_price in item_prices_nl:
        item_prices_dict_nl.setdefault(
            item_price.item_code, []).append(item_price)

    template_data = []

    # logger.info("Total item templates: %s" % len(item_templates))
    # logger.info("Total item_variants: %s" % len(item_variants))
    # logger.info("Total batches: %s" % len(batches))
    # logger.info("Total item_prices: %s" % len(item_prices))

    
    total_batches_l_f = 0
    total_batches_p_f = 0
    total_qty_f = 0

    item_templates += item_without_template

    for item_template in item_templates:
        template = item_template.item_code
        variants = variants_dict.get(template, [])

        # logger.info("Template: %s" % template)
        # logger.info("Variants len: %s" % len(variants))

        packed_assortment_p = {}
        variant_batches_count_p = []
        packed_assortment_l = {}
        variant_batches_count_l = []
        batch_qty = 0
        total_qty = 0
        total_batches_l = 0
        total_batches_p = 0


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
                total_qty +=  variant_batches['total_qty']
                total_qty_f += variant_batches['total_qty']
                enabled_batches = variant_batches['enabled_batches']
                disabled_batches = variant_batches['disabled_batches']
                enabled_batches_len = len(enabled_batches)
                disabled_batches_len = len(disabled_batches)

                if enabled_batches_len > 0:
                    total_batches_l += enabled_batches_len
                    total_batches_l_f += enabled_batches_len
                    # packed_assortment_l[attribute_value] = enabled_batches_len

                    variant_batches_count_l.append(
                        str(attribute_value) + '/' + str(enabled_batches_len))
                if disabled_batches_len > 0:
                    total_batches_p += disabled_batches_len
                    total_batches_p_f += disabled_batches_len
                    variant_batches_count_p.append(
                        str(attribute_value) + '/' + str(disabled_batches_len))
                # packed_assortment_p[attribute_value] = disabled_batches_len

        cash_rate = 0
        sn_rate = 0
        no_less_rate = 0
        
        item_price = item_prices_dict_cash.get(template, [])
        if len(item_price):
            cash_rate = item_price[0].price_list_rate


        item_price = item_prices_dict_sn.get(template, [])
        if len(item_price):
            sn_rate = item_price[0].price_list_rate

        item_price = item_prices_dict_nl.get(template, [])
        if len(item_price):
            no_less_rate = item_price[0].price_list_rate

        if len(variant_batches_count_p) or len(variant_batches_count_l):
            template_data.append({
                'template': template,
                'item_name': item_template.item_name,
                'group': item_template.item_group,
                'packed_assortment': ", ".join(variant_batches_count_p),
                'loose_assortment': ", ".join(variant_batches_count_l),
                'total_batches': total_batches_l + total_batches_p,
                'total_qty': total_qty,
                'cash_rate': cash_rate,
                'sn_rate': sn_rate,
                'no_less_rate': no_less_rate,
                'batch_qty': batch_qty,
            })

    template_data = sorted(template_data, key=lambda x: x['batch_qty'], reverse=True)

    template_data.append({
        'template': 'Total',
        'group': '',
        'packed_assortment': total_batches_p_f,
        'loose_assortment': total_batches_l_f,
        'total_batches': total_batches_p_f + total_batches_l_f,
        'cash_rate': 0,
        'total_qty': total_qty_f,
    })

    # logger.info("End of get_template_data")

    return template_data
