
from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.utils import cint, flt

from erpnext.stock.doctype.batch.batch import get_batch_qty
from erpnext.stock.get_item_details import get_item_details


@frappe.whitelist()
def get_so_items(doc, order_entry_item):

    data = []

    if isinstance(doc, str):
        # frappe.msgprint(doc)
        doc = json.loads(doc)

    doc = frappe._dict(doc)

    # frappe.msgprint("so items")
    # frappe.msgprint(str(doc['items']))
    # frappe.msgprint(str(doc))

    if isinstance(order_entry_item, str):
        # frappe.msgprint(order_entry_item)
        order_entry_item = json.loads(order_entry_item)

    # item_codes = []
    # item_codes = [d.item_code for d in doc.items]
    item_codes = list(map(lambda d: d['item_code'], doc['items']))

    order_entry_item = frappe._dict(order_entry_item)
    # order_entry_item_qty = order_entry_item.qty
    item_code = order_entry_item.item_code

    item = frappe.get_cached_doc("Item", item_code)

    if item.has_variants:
        abbr = 'S'
        category_attribute_value = frappe.db.get_value("Item Attribute Value", 
                                                       filters={
                                                            'parent': 'Category', 
                                                            'abbr': abbr
                                                        }, 
                                                        fieldname='attribute_value')

        parent_items = frappe.get_list("Item Variant Attribute", 
                                        filters={
                                            'attribute_value': category_attribute_value
                                        },
                                        order_by='creation',
                                        pluck='parent')

        filtered_items = list(filter(lambda d: d not in item_codes, parent_items))

        variant_items = frappe.get_list("Item", filters={
                                            'variant_of': item_code,
                                            # 'name': ['in', parent_items]
                                            'name': ['in', filtered_items]
                                        })

        for row in variant_items:
            batches = frappe.db.sql(
                """select batch_no, sum(actual_qty) as qty
                from `tabStock Ledger Entry`
                where is_cancelled = 0 and item_code = %s
                group by batch_no
                having sum(actual_qty) > 0
                order by qty desc""", row.name,
                as_dict=1,
            )

            for _ in range(cint(order_entry_item.qty) or 1):
                so_item = frappe._dict({
                    'item_code': row.name,
                    'qty': 1,
                })

                if len(batches):
                    batch = batches[0]
                    # so_item.batch_no = batch.batch_no
                    so_item.qty = batch.qty

                data.append(so_item)

    else:
        if item_code not in item_codes:
            batches = frappe.db.sql(
                """select batch_no, sum(actual_qty) as qty
                from `tabStock Ledger Entry`
                where is_cancelled = 0 and item_code = %s
                group by batch_no
                having sum(actual_qty) > 0
                order by qty desc""", item_code,
                as_dict=1,
            )

            for _ in range(cint(order_entry_item.qty) or 1):
                so_item = frappe._dict({
                    'item_code': item_code,
                    'qty': 1,
                })

                if len(batches):
                    batch = batches[0]
                    # so_item.batch_no = batch.batch_no
                    so_item.qty = batch.qty

                data.append(so_item)

    response = frappe._dict()

    response['success'] = True
    response['data'] = data

    return response


@frappe.whitelist()
def before_save(doc, method):
    set_items_based_on_order_entry_items(doc)


def set_items_based_on_order_entry_items(doc):

    # item_codes = [d.item_code for d in doc.items]
    item_codes = list(map(lambda d: d.item_code, doc.items))

    for order_entry_item in doc.order_entry_items:
        item_code = order_entry_item.item_code

        item = frappe.get_cached_doc("Item", item_code)

        if item.has_variants:
            abbr = 'S'
            category_attribute_value = frappe.db.get_value("Item Attribute Value", 
                                                        filters={
                                                                'parent': 'Category', 
                                                                'abbr': abbr
                                                            }, 
                                                            fieldname='attribute_value')

            parent_items = frappe.get_list("Item Variant Attribute", 
                                            filters={
                                                'attribute_value': category_attribute_value
                                            },
                                            order_by='creation',
                                            pluck='parent')

            filtered_items = list(filter(lambda d: d not in item_codes, parent_items))

            variant_items = frappe.get_list("Item", filters={
                                                'variant_of': item_code,
                                                # 'name': ['in', parent_items]
                                                'name': ['in', filtered_items]
                                            })

            for row in variant_items:
                batches = frappe.db.sql(
                    """select batch_no, sum(actual_qty) as qty
                    from `tabStock Ledger Entry`
                    where is_cancelled = 0 and item_code = %s
                    group by batch_no
                    having sum(actual_qty) > 0
                    order by qty desc""", row.name,
                    as_dict=1,
                )

                for _ in range(cint(order_entry_item.qty) or 1):
                    # so_item = frappe._dict({
                    #     'item_code': row.name,
                    #     'qty': 1
                    # })
                    so_item = get_item_details({
                        'item_code': row.name,
                        'company': doc.company,
                        'doctype': doc.doctype,
                    })

                    if len(batches):
                        batch = batches[0]
                        # so_item.batch_no = batch.batch_no
                        so_item.qty = batch.qty

                    doc.append('items', so_item)

        else:
            if item_code not in item_codes:
                batches = frappe.db.sql(
                    """select batch_no, sum(actual_qty) as qty
                    from `tabStock Ledger Entry`
                    where is_cancelled = 0 and item_code = %s
                    group by batch_no
                    having sum(actual_qty) > 0
                    order by qty desc""", item_code,
                    as_dict=1,
                )

                for _ in range(cint(order_entry_item.qty) or 1):
                    # so_item = frappe._dict({
                    #     'item_code': item_code,
                    #     'qty': 1
                    # })
                    so_item = get_item_details({
                        'item_code': item_code,
                        'company': doc.company,
                        'doctype': doc.doctype,
                    })

                    if len(batches):
                        batch = batches[0]
                        # so_item.batch_no = batch.batch_no
                        so_item.qty = batch.qty

                    doc.append('items', so_item)
