from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content
from erpnext.stock.get_item_details import get_item_details
from erpnext.accounts.party import set_taxes

class DeliveryNoteImport(Document):

    def before_save(self):
        self.import_from_google_sheets("https://docs.google.com/spreadsheets/d/13iTayL1eLFPAEizkHTPuXSDQaJJKMatihArfTe4Dyg4/edit#gid=0")
        
    def import_from_google_sheets(self, sheet_url):
        # Fetch data from Google Sheets
        content = get_csv_content_from_google_sheets(sheet_url)
        data = read_csv_content(content)
        keys = data[0]

        # Group rows by customer
        customer_grouped_data = {}
        for row in data[1:]:
            row_dict = {keys[i]: value for i, value in enumerate(row)}
            customer_name = row_dict['Customer Name']

            if customer_name in customer_grouped_data:
                customer_grouped_data[customer_name].append(row_dict)
            else:
                customer_grouped_data[customer_name] = [row_dict]

        errors = []
        total_created = 0

        # Fetch the default company's currency
        default_company = frappe.defaults.get_user_default("Company")
        default_currency = frappe.get_value("Company", default_company, "default_currency")

        for customer_name, rows in customer_grouped_data.items():
            items = []

            for row in rows:
                batch_id = row['Batch']
                rate = row['Rate']
                price_list = row.get('Price List', 'Cash')  # default to 'Cash' if not provided
                warehouse = row['Warehouse']

                # Fetch item_code and batch quantity from the Batch doctype
                batch_data = frappe.get_doc('Batch', batch_id)
                item_code = batch_data.item
                batch_quantity = batch_data.batch_qty

                # Fetch item details
                item_details = get_item_details({
                    "item_code": item_code,
                    "warehouse": warehouse,
                    "customer": customer_name,
                    "price_list": price_list,
                    "company": default_company,
                    "doctype": "Delivery Note",
                    "date": now_datetime().date(),
                    "qty": batch_quantity
                })

                rate = rate if rate else item_details.get('price_list_rate')

                items.append({
                    'item_code': item_code,
                    'qty': batch_quantity,
                    'price_list_rate': rate,
                    'discount_percentage': item_details.get('discount_percentage', 0),
                    'batch_no': batch_id,
                    'warehouse': warehouse
                })

            try:
                # Create delivery note
                new_delivery_note = frappe.get_doc({
                    'doctype': 'Delivery Note',
                    'customer': customer_name,
                    'currency': default_currency,
                    'items': items,
                    'selling_price_list': price_list
                })

                # Set taxes
                set_taxes(new_delivery_note, "Delivery Note")

                new_delivery_note.insert()
                total_created += 1

            except Exception as e:
                error_message = f"{customer_name}: {str(e)}"
                errors.append(error_message)

        # Update fields
        self.total_delivery_notes_created = total_created
        self.last_created_on = now_datetime()

        if errors:
            frappe.throw(msg='\n'.join(errors), title="Please rectify these errors")

