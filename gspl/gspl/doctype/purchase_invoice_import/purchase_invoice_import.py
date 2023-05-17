# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

# import frappe


from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content

from frappe.utils import logger
import json
import ast
import traceback

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

class PurchaseInvoiceImport(Document):
    
	@frappe.whitelist()
	def before_validate(doc):
		arvind_url = 'https://docs.google.com/spreadsheets/d/1ffZ04U9U0vyTORGEKPCHB3ONeKfUMZ4VVfPvpfMsy_U/edit#gid=2027730903'
		vimal_url = 'https://docs.google.com/spreadsheets/d/1ffZ04U9U0vyTORGEKPCHB3ONeKfUMZ4VVfPvpfMsy_U/edit#gid=229283959'
		others_url = 'https://docs.google.com/spreadsheets/d/1ffZ04U9U0vyTORGEKPCHB3ONeKfUMZ4VVfPvpfMsy_U/edit#gid=0'
		url = url = arvind_url if doc.import_type == 'Arvind' else vimal_url if doc.import_type == 'Vimal' else others_url if doc.import_type == 'Others' else ''
		content = None
		content = get_csv_content_from_google_sheets(url)
		data = read_csv_content(content)
		keys = data[0]
		i_dict_list = [] # Initial Dict List
		dict_list = []

		for row in data[1:]:
			row_dict = {}
			for i, value in enumerate(row):
				row_dict[keys[i]] = value

			i_dict_list.append(row_dict)

		if doc.import_type == "Arvind":
			dict_list = doc.get_arvind_dict(i_dict_list)
		elif doc.import_type == 'Vimal':
			dict_list = doc.get_vimal_dict(i_dict_list)
		elif doc.import_type == 'Others':
			for row_dict in i_dict_list:
				final = row_dict['Sort Number'] 
				if row_dict['Shade']:  # Shade
					final =final+'-' + row_dict['Shade'] 
				row_dict['Final Item'] = final
			dict_list = i_dict_list


		# Create a new list called items based on dict_list
		item_codes = set([row_dict['Sort Number'] for row_dict in dict_list])
		existing_item_codes = set([item['name'] for item in frappe.get_all('Item')])
		new_item_codes = {code.upper() for code in item_codes} - {code.upper() for code in existing_item_codes}


		items_items = []

		for item_code in new_item_codes:
			shades_exist = any([row_dict['Shade'] for row_dict in dict_list if row_dict['Sort Number'] == item_code])
			has_variants = 1 if shades_exist else 0
			item_group = "Temp"
			brand = next((row_dict['Brand'] for row_dict in dict_list if row_dict['Sort Number'] == item_code), None)
			gst_hsn_code = next((row_dict['HSN_CODE'] for row_dict in dict_list if row_dict['Sort Number'] == item_code), None)
			stock_uom = next((row_dict['stock_uom'] for row_dict in dict_list if row_dict['Sort Number'] == item_code), None)

			items_items.append({
				'item_code': item_code,
				'item_name': item_code,
				'item_group': item_group,
				'gst_hsn_code': gst_hsn_code,
				'has_variants': has_variants,
				'brand': brand,
				'stock_uom': stock_uom
			})



		# Create a new list called variants based on dict_list
		item_codes = set([row_dict['Final Item'] for row_dict in dict_list])
		existing_item_codes = set([item['name'] for item in frappe.get_all('Item')])
		new_item_codes = {code.upper() for code in item_codes} - {code.upper() for code in existing_item_codes}

		variants = []

		for item_code in new_item_codes:
			shades_exist = any([row_dict['Shade'] for row_dict in dict_list if row_dict['Final Item'] == item_code])
			attribute_value = next((str(row_dict['Shade']) for row_dict in dict_list if row_dict['Final Item'] == item_code), "NA") if shades_exist else None
			variant_of = next((row_dict['Sort Number'] for row_dict in dict_list if row_dict['Final Item'] == item_code), None)
			item_group = "Temp"
			brand = next((row_dict['Brand'] for row_dict in dict_list if row_dict['Final Item'] == item_code), None)
			gst_hsn_code = next((row_dict['HSN_CODE'] for row_dict in dict_list if row_dict['Final Item'] == item_code), None)
			stock_uom = next((row_dict['stock_uom'] for row_dict in dict_list if row_dict['Final Item'] == item_code), None)

			if shades_exist:
				variants.append({
					'item_code': item_code,
					'item_name': item_code,
					'variant_of': variant_of,
					'item_group': item_group,
					'gst_hsn_code': gst_hsn_code,
					'attribute_value': attribute_value,
					'brand': brand,
					'stock_uom': stock_uom
				})

			logger.debug(str(variants))




		# Create a new list called batches based on dict_list
		batch_ids = set([row_dict['Barcode'] for row_dict in dict_list])
		existing_batch_ids = set([batch['name'] for batch in frappe.get_all('Batch')])
		new_batch_ids = batch_ids - existing_batch_ids


		batches = []
		for row_dict in dict_list:
			batch_no = row_dict.get('Barcode')
			if batch_no in new_batch_ids:
				item_code = row_dict.get('Final Item')
				if batch_no and item_code:
					batches.append({
						'batch_no': batch_no,
						'item_code': item_code
					})



		

		#Create All Things
		doc.create_items(items_items)
		doc.create_variants(variants)
		doc.create_batches(batches)
		doc.create_purchase_invoice(dict_list)
		

	def get_arvind_dict(doc,i_dict_list):
		# Loop over each row in dict2
		dict_list = []
		for dict2 in i_dict_list:

			# Implementing the logic
			dict1 = {'Supplier Name': '', 'Supplier Invoice No': '', 'INVOICE_DATE': '', 'LR Num': '', 'LR Date': '',
         'case_number': '', 'Sort Number': '', 'Shade': '', 'Barcode': '', 'Brand': 'Arvind', 'HSN_CODE': '',
         'Quantity': '', 'Rate': '', 'stock_uom': 'Meter', 'Accepted Warehouse': 'Kanhaiya Express - GSPL', 'Final Item': ''}
			dict1['Supplier Name'] = 'Arvind Limited'
			dict1['Supplier Invoice No'] = dict2['Plant Invoice / Line'].split('/')[0]
			dict1['INVOICE_DATE'] = dict2['Plant Invoice Date']
			dict1['LR Num'] = dict2['LR No.']
			dict1['LR Date'] = dict2['LR Date']
			dispatch_so_line = dict2['Dispatch SO/Line'].split('/')
			dict1['case_number'] = dict2['HU No.']
			dict1['Sort Number'] = dict2['SORT']
			dict1['Shade'] = dispatch_so_line[1]
			dict1['Barcode'] = dict2['Batch No.']
			dict1['HSN_CODE'] = dict2['HSN Code']
			dict1['Quantity'] = dict2['Batch Qty.']
			if float(dict2['Net Rate Per mts']) != 0:
				dict1['Rate'] = dict2['Net Rate Per mts']
			else:
				rate = next((row['Net Rate Per mts'] for row in i_dict_list if row['Dispatch SO/Line'] == dict2['Dispatch SO/Line'] and float(row['Net Rate Per mts']) != 0), '')
				dict1['Rate'] = rate
			dict1['stock_uom'] = 'Meter'
			dict1['Accepted Warehouse'] = 'Kanhaiya Express - GSPL'
			
			final = dict1['Sort Number']
			if dict1['Shade']:  # Shade
				final +='-' + dict1['Shade'] 
			dict1['Final Item'] = final
			dict_list.append(dict1)

		return dict_list
	

	def get_vimal_dict(doc,i_dict_list):
		# Loop over each row in dict2
		dict_list = []
		for dict3 in i_dict_list:

			# Implementing the logic
			dict1 = {'Supplier Name': '', 'Supplier Invoice No': '', 'INVOICE_DATE': '', 'LR Num': '', 'LR Date': '',
         'case_number': '', 'Sort Number': '', 'Shade': '', 'Barcode': '', 'Brand': 'Arvind', 'HSN_CODE': '',
         'Quantity': '', 'Rate': '', 'stock_uom': 'Meter', 'Accepted Warehouse': 'Kanhaiya Express - GSPL', 'Final Item': ''}
			dict1['Supplier Name'] = 'Reliance Industries Limited'
			dict1['Supplier Invoice No'] = dict3['TAX_INVOICE_NO']
			dict1['INVOICE_DATE'] = dict3['INVOICE_DATE']
			dict1['LR Num'] = dict3['TRANSPORTER_CN']
			dict1['LR Date'] = dict3['TRANSPORTER_CN_DATE']
			dict1['case_number'] = dict3['CASE_NO'][7:]
			material_split = dict3['MATERIAL'].split('F')
			dict1['Sort Number'] = material_split[1][3:].lstrip('0')
			dict1['Shade'] = material_split[2].lstrip('0')
			dict1['Barcode'] = dict3['BARCODE']
			dict1['Brand'] = 'Vimal'
			dict1['HSN_CODE'] = dict3['HSN_CODE'].replace(" ", "")
			dict1['Quantity'] = dict3['GROSS_METERS']
			dict1['Rate'] = float(dict3['GROSS_AMT']) / (1.05 * float(dict3['GROSS_METERS']))
			dict1['stock_uom'] = 'Meter'
			dict1['Accepted Warehouse'] = 'Inland World Logistics - GSPL'
			final = dict1['Sort Number']
			if dict1['Shade']:  # Shade
				final +='-' + dict1['Shade'] 
			dict1['Final Item'] = final
			dict_list.append(dict1)


		return dict_list




	def create_items(doc,items):

		total_created = 0
		errors = []

		for item in items:
			try:
				# create the item
				new_item = frappe.get_doc({
					'doctype': 'Item',
					'item_code': item['item_code'],
					'item_name': item['item_name'],
					'item_group': "Temp",
					'gst_hsn_code': item['gst_hsn_code'],
					'has_variants': item['has_variants'],
					'brand': item['brand'],
					'stock_uom': item['stock_uom']
				})

				new_item.insert()
				total_created += 1
			except Exception as e:
				# catch the error and store it in the 'errors' list
				frappe.msgprint(str(e))
				error_message = f"{item['item_code']}: {str(e)}"
				errors.append(error_message)

		doc.total_items_created =  total_created
		if errors:
			frappe.throw(msg=error_message, title="Please Rectify These Errorsin Items", as_list=True)
			


	def create_variants(doc,variants):

		total_created = 0
		errors = []

		for item in variants:
			try:
				# create the item
				new_item = frappe.get_doc({
					'doctype': 'Item',
					'item_code': item['item_code'],
					'item_name': item['item_name'],
					'item_group': item['item_group'],
					'gst_hsn_code': item['gst_hsn_code'],
					'variant_of': item['variant_of'],
					'brand': item['brand'],
					'stock_uom': item['stock_uom'],
					"attributes": [{
						"attribute": "Shade",
						"attribute_value": item['attribute_value']
					}]
				})

				new_item.insert()
				total_created += 1
			except Exception as e:
				# catch the error and store it in the 'errors' list
				error_message = f"{item['item_code']}: {str(e)}"
				errors.append(error_message)

		doc.total_variants_created =  total_created
		if errors:
			frappe.throw(msg=error_message, title="Please Rectify These Errors in variants", as_list=True)
			

	def create_batches(doc,batches):

		total_created = 0
		errors = []

		for batch in batches:
			try:
				# create the item
				new_batch = frappe.get_doc({
					'doctype': 'Batch',
					'item': batch['item_code'],
					'batch_id': batch['batch_no'],
				})

				new_batch.insert()
				total_created += 1
			except Exception as e:
				# catch the error and store it in the 'errors' list
				error_message = f"{batch['batch_no']}: {str(e)}"
				errors.append(error_message)

		doc.total_batches_created =  total_created
		if errors:
			frappe.throw(msg=error_message, title="Please Rectify These Errors in Batches", as_list=True)




	def create_purchase_invoice(doc,dict_list):

		supplier_invoice_dict = {}
		for row in dict_list:
			supplier_name = row['Supplier Name']
			supplier_invoice_no = row['Supplier Invoice No']
			lr_number = row['LR Num']
			lr_date = row['LR Date']
			bill_date = row['INVOICE_DATE']
			

			# Create a key for grouping the rows based on supplier name, supplier invoice no, invoice date, lr num, and lr date
			key = f"{supplier_name}-{supplier_invoice_no}"

			# Check if this key already exists in the supplier invoice dict
			if key in supplier_invoice_dict:
				# If yes, add the row to the existing purchase invoice
				items = supplier_invoice_dict[key]['items']
				item = {
					'item_code': row['Final Item'],
					'item_name': row['Final Item'],
					'qty': row['Quantity'],
					'price_list_rate': row['Rate'],
					'uom': row['stock_uom'],
					'batch_no': row['Barcode'],
					'case_number': row['case_number'],
					'expense_account': 'Stock In Hand - GSPL',
					'warehouse': row['Accepted Warehouse'],
					'gst_hsn_code': row['HSN_CODE']
				}
				items.append(item)
			else:
				# If no, create a new purchase invoice
				supplier_invoice_dict[key] = {
					'supplier_name': supplier_name,
					'supplier_invoice_no': supplier_invoice_no,
					'lr_number': lr_number,
					'lr_date': lr_date,
					'bill_date': bill_date,
					'items': [
						{
							'item_code': row['Final Item'],
							'item_name': row['Final Item'],
							'qty': row['Quantity'],
							'price_list_rate': row['Rate'],
							'uom': row['stock_uom'],
							'batch_no': row['Barcode'],
							'case_number': row['case_number'],
							'expense_account': 'Stock In Hand - GSPL',
							'warehouse': row['Accepted Warehouse'],
							'gst_hsn_code': row['HSN_CODE']
							
						}
					]
				}

		# Initialize variables
		total_created = 0
		errors = []
		
		# Create purchase invoice documents for each supplier invoice
		for key in supplier_invoice_dict:
			supplier_invoice = supplier_invoice_dict[key]
			supplier_name = supplier_invoice['supplier_name']
			supplier_invoice_no = supplier_invoice['supplier_invoice_no']
			# try:
			existing_purchase_invoices = frappe.get_all('Purchase Invoice', filters={
				'supplier': supplier_name,
				'bill_no': supplier_invoice_no,
				'docstatus': ['!=', 2]  # Only check for non cancelled purchase invoices
			})
			if not existing_purchase_invoices:
				d = frappe.new_doc('Purchase Invoice')
				d.supplier = supplier_name
				d.bill_no = supplier_invoice_no
				d.lr_number = supplier_invoice['lr_number'] + ' ' + supplier_invoice['lr_date']
				d.bill_date = supplier_invoice['bill_date']
				# doc.taxes_and_charges = 'GST 18%'
				# doc.tax_id = 'GST 18%'
				temp_items = supplier_invoice['items']
				for item in temp_items:
					d.append('items', {
							'item_code': item['item_code'],
							'item_name': item['item_name'],
							'gst_hsn_code': item['gst_hsn_code'],
							'qty':item['qty'],
							'price_list_rate': item['price_list_rate'],
							'uom': item['uom'],
							'batch_no': item['batch_no'],
							'case_number': item['case_number'],
							'expense_account': 'Stock In Hand - GSPL',
							'warehouse': item['warehouse']
						}
					)
				d.save()
				total_created += 1


		doc.total_pi_created =  total_created
