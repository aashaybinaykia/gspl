from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content
from frappe.utils import logger
import json
from datetime import datetime

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

class PurchaseOrderImport(Document):

    @frappe.whitelist()
    def before_validate(doc):
        url = 'https://docs.google.com/spreadsheets/d/1H1oW6DASH4UomQZQ8LDHRvrft0N80OkCbKz-xVO0PBI/edit?usp=sharing'
        content = get_csv_content_from_google_sheets(url)
        data = read_csv_content(content)
        keys = data[0]
        i_dict_list = []

        # Populate initial dictionary list
        for row in data[1:]:
            row_dict = {keys[i]: value for i, value in enumerate(row)}
            row_dict['Final Item'] = row_dict['Template']
            if row_dict.get('Shade'):
                row_dict['Final Item'] += f"-{row_dict['Shade']}"
            i_dict_list.append(row_dict)

        # Process new and duplicate items
        dict_list = i_dict_list
        item_codes = set(row_dict['Template'] for row_dict in dict_list)
        existing_item_codes = set(item['name'] for item in frappe.get_all('Item'))
        new_item_codes = {code.upper() for code in item_codes} - {code.upper() for code in existing_item_codes}
        duplicate_item_codes = existing_item_codes.intersection(item_codes)

        for item_code in duplicate_item_codes:
            brand_dict_list = next((row_dict['Brand'] for row_dict in dict_list if row_dict['Template'] == item_code), None)
            existing_brand = frappe.get_value('Item', {'name': item_code}, 'brand')
            if brand_dict_list.upper() != existing_brand.upper():
                frappe.throw(f"The brand of item {item_code} in dict_list is different from the existing brand")

        # Prepare item creation
        items_to_create = []
        for item_code in new_item_codes:
            row = next(row_dict for row_dict in dict_list if row_dict['Template'] == item_code)
            items_to_create.append({
                'item_code': item_code,
                'item_name': item_code,
                'item_group': "Temp",
                'gst_hsn_code': row.get('HSN_CODE'),
                'has_variants': 1 if row.get('Shade') else 0,
                'brand': row.get('Brand'),
                'stock_uom': row.get('stock_uom')
            })

        # Prepare variant creation
        variant_codes = set(row_dict['Final Item'] for row_dict in dict_list)
        new_variant_codes = {code.upper() for code in variant_codes} - {code.upper() for code in existing_item_codes}
        variants_to_create = []

        for variant_code in new_variant_codes:
            row = next(row_dict for row_dict in dict_list if row_dict['Final Item'].upper() == variant_code.upper())
            variants_to_create.append({
                'item_code': variant_code,
                'item_name': variant_code,
                'variant_of': row['Template'],
                'item_group': "Temp",
                'gst_hsn_code': row.get('HSN_CODE'),
                'attribute_value': row.get('Shade', "NA"),
                'brand': row.get('Brand'),
                'stock_uom': row.get('stock_uom'),
                'supplier_item_name': row.get('SUPPLIER_ITEM_NAME')
            })

        # Create items, variants, and purchase orders
        doc.create_items(items_to_create)
        doc.create_variants(variants_to_create)
        doc.create_purchase_order(dict_list)

    def create_items(doc, items):
        total_created = 0
        errors = []

        for item in items:
            try:
                new_item = frappe.get_doc({
                    'doctype': 'Item',
                    'item_code': item['item_code'],
                    'item_name': item['item_name'],
                    'item_group': item['item_group'],
                    'gst_hsn_code': item['gst_hsn_code'],
                    'has_variants': item['has_variants'],
                    'brand': item['brand'],
                    'stock_uom': item['stock_uom']
                })
                new_item.insert()
                total_created += 1
            except Exception as e:
                error_message = f"{item['item_code']}: {str(e)}"
                errors.append(error_message)

        doc.total_items_created = total_created
        if errors:
            frappe.throw(msg=errors, title="Errors in Items", as_list=True)

    def create_variants(doc, variants):
        total_created = 0
        errors = []

        for variant in variants:
            try:
                new_item = frappe.get_doc({
                    'doctype': 'Item',
                    'item_code': variant['item_code'],
                    'item_name': variant['item_name'],
                    'variant_of': variant['variant_of'],
                    'item_group': variant['item_group'],
                    'gst_hsn_code': variant['gst_hsn_code'],
                    'brand': variant['brand'],
                    'stock_uom': variant['stock_uom'],
                    'attributes': [{
                        'attribute': 'Shade',
                        'attribute_value': variant['attribute_value']
                    }],

                	'supplier_item_name': variant['supplier_item_name']
                })
                new_item.insert()
                total_created += 1
            except Exception as e:
                error_message = f"{variant['item_code']}: {str(e)}"
                errors.append(error_message)

        doc.total_variants_created = total_created
        if errors:
            frappe.throw(msg=errors, title="Errors in Variants", as_list=True)

    def create_purchase_order(doc, dict_list):
        supplier_invoice_dict = {}

        for row in dict_list:
            supplier_name = row['Supplier Name']
            key = supplier_name

            if key not in supplier_invoice_dict:
                supplier_invoice_dict[key] = {
                    'supplier_name': supplier_name,
                    'transaction_date': datetime.now().date(),
                    'items': []
                }

            supplier_invoice_dict[key]['items'].append({
                'item_code': row['Final Item'],
                'item_name': row['Final Item'],
                'qty': row['Quantity'],
                'price_list_rate': row['Rate'],
                'uom': row['stock_uom'],
                'brand': row['Brand'],
                'expense_account': 'Stock In Hand - GSPL',
                'warehouse': 'Shop - GSPL',
                'gst_hsn_code': row['HSN_CODE'],
                'supplier_item_name': row['SUPPLIER_ITEM_NAME']
            })

        total_created = 0
        errors = []

        for key, invoice in supplier_invoice_dict.items():
            try:
                d = frappe.new_doc('Purchase Order')
                d.supplier = invoice['supplier_name']
                d.transaction_date = invoice['transaction_date']
                d.schedule_date = datetime.now().date()

                for item in invoice['items']:
                    d.append('items', item)

                d.insert()
                total_created += 1
            except Exception as e:
                errors.append(str(e))

        doc.total_pi_created = total_created
        if errors:
            frappe.throw(msg=errors, title="Errors in Purchase Orders", as_list=True)
