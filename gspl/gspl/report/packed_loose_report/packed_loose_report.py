# Copyright (c) 2026, GSPL
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import flt, cint

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
    filters = filters or {}
    
    # --- 1. Base Item Filters ---
    base_filters = {}
    if filters.get('brand'):
        base_filters['brand'] = filters.get('brand')
    if filters.get('group'):
        base_filters['item_group'] = filters.get('group')

    # --- 2. Fetch Templates & Standalones ---
    template_filters = base_filters.copy()
    template_filters['has_variants'] = 1
    templates = frappe.get_all("Item", filters=template_filters, fields=["name", "item_name", "item_group"])
    
    standalone_filters = base_filters.copy()
    standalone_filters['has_variants'] = 0
    standalone_filters['variant_of'] = ["in", ["", None]]
    standalones = frappe.get_all("Item", filters=standalone_filters, fields=["name", "item_name", "item_group"])

    all_parents = templates + standalones
    parent_names = [d.name for d in all_parents]

    if not parent_names:
        return []

    # --- 3. Fetch Variants ---
    variants = []
    if templates:
        template_names = [d.name for d in templates]
        variants = frappe.get_all(
            "Item",
            filters={"variant_of": ["in", template_names]},
            fields=["name", "variant_of", "attributes.attribute_value"],
            order_by="attributes.attribute_value asc"
        )

    # FIX: Wrap in frappe._dict so dot notation (v.name) works smoothly
    for s in standalones:
        variants.append(frappe._dict({
            "name": s.name,
            "variant_of": s.name,
            "attribute_value": "NA"
        }))

    variant_names = [v.name for v in variants]
    if not variant_names:
        return []

    # --- 4. Fetch Active Batches (Safely via Query Builder) ---
    min_qty = flt(filters.get('min_qty', 0))
    max_qty = flt(filters.get('max_qty', 10000))
    if max_qty <= min_qty:
        max_qty = 10000

    batch_table = frappe.qb.DocType("Batch")
    query = (
        frappe.qb.from_(batch_table)
        .select(batch_table.item, batch_table.batch_qty, batch_table.disabled)
        .where(batch_table.item.isin(variant_names))
        .where(batch_table.batch_qty > min_qty)
        .where(batch_table.batch_qty < max_qty)
    )
    if filters.get('content'):
        query = query.where(batch_table.content == filters.get('content'))

    batches = query.run(as_dict=True)

    # Group Batches in Memory
    batch_map = {}
    for b in batches:
        if b.item not in batch_map:
            batch_map[b.item] = {'total_qty': 0.0, 'enabled': 0, 'disabled': 0}
            
        batch_map[b.item]['total_qty'] += flt(b.batch_qty)
        if b.disabled:
            batch_map[b.item]['disabled'] += 1
        else:
            batch_map[b.item]['enabled'] += 1

    # --- 5. Fetch Prices (Unified Query) ---
    prices = frappe.get_all(
        "Item Price",
        filters={
            "item_code": ["in", parent_names],
            "price_list": ["in", ["Cash", "Super Net", "No Less"]]
        },
        fields=["item_code", "price_list", "price_list_rate"],
        order_by="valid_from desc"
    )

    price_map = {}
    for p in prices:
        if p.item_code not in price_map:
            price_map[p.item_code] = {}
        # Ordered desc, so first seen is latest
        if p.price_list not in price_map[p.item_code]:
            price_map[p.item_code][p.price_list] = flt(p.price_list_rate)

    # --- 6. Construct Final Data ---
    variants_by_parent = {}
    for v in variants:
        variants_by_parent.setdefault(v.variant_of, []).append(v)

    template_data = []
    grand_total_l_batches = 0
    grand_total_p_batches = 0
    grand_total_qty = 0.0

    for parent in all_parents:
        parent_name = parent.name
        vars_for_parent = variants_by_parent.get(parent_name, [])

        p_assortment = []
        l_assortment = []
        parent_total_qty = 0.0
        parent_l_batches = 0
        parent_p_batches = 0

        for v in vars_for_parent:
            b_data = batch_map.get(v.name)
            if not b_data:
                continue

            attr_val = v.attribute_value or "NA"
            parent_total_qty += b_data['total_qty']
            
            if b_data['enabled'] > 0:
                parent_l_batches += b_data['enabled']
                l_assortment.append(f"{attr_val}/{b_data['enabled']}")
                
            if b_data['disabled'] > 0:
                parent_p_batches += b_data['disabled']
                p_assortment.append(f"{attr_val}/{b_data['disabled']}")

        if parent_l_batches > 0 or parent_p_batches > 0:
            p_rates = price_map.get(parent_name, {})
            
            template_data.append({
                'template': parent_name,
                'item_name': parent.item_name,
                'group': parent.item_group,
                'packed_assortment': ", ".join(p_assortment),
                'loose_assortment': ", ".join(l_assortment),
                'total_batches': parent_l_batches + parent_p_batches,
                'total_qty': parent_total_qty,
                'cash_rate': p_rates.get('Cash', 0.0),
                'sn_rate': p_rates.get('Super Net', 0.0),
                'no_less_rate': p_rates.get('No Less', 0.0),
                'sort_qty': parent_total_qty # Hidden key for sorting
            })
            
            grand_total_l_batches += parent_l_batches
            grand_total_p_batches += parent_p_batches
            grand_total_qty += parent_total_qty

    # --- 7. Sort & Append Totals ---
    template_data = sorted(template_data, key=lambda x: x['sort_qty'], reverse=True)

    template_data.append({
        'template': 'Total',
        'group': '',
        'packed_assortment': str(grand_total_p_batches),
        'loose_assortment': str(grand_total_l_batches),
        'total_batches': grand_total_p_batches + grand_total_l_batches,
        'cash_rate': 0.0,
        'sn_rate': 0.0,
        'no_less_rate': 0.0,
        'total_qty': grand_total_qty,
    })

    return template_data