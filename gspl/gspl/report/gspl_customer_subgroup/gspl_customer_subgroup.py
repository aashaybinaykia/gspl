import frappe
from frappe import _

def execute(filters=None):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    item_group = filters.get("item_group")
    brand = filters.get("brand")
    territory = filters.get("territory")

    # Get all the delivery notes between the "from" and "to" dates
    delivery_note_filters = {'posting_date': ['between', [from_date, to_date]]}
	
    if territory:
        delivery_note_filters['territory'] = territory
    delivery_notes = frappe.get_all('Delivery Note', filters=delivery_note_filters, fields=['name', 'posting_date', 'customer', 'territory'])

    # Initialize data dictionary with customer names as keys
    data_dict = {}

    # Extract all the delivery note items from these delivery notes
    for delivery_note in delivery_notes:
        item_filters = {'parent': delivery_note.name}
        if item_group:
            item_filters['item_group'] = item_group
        if brand:
            item_filters['brand'] = brand
        items = frappe.get_all('Delivery Note Item', filters=item_filters, 
                               fields=['net_amount', 'qty', 'returned_qty', 'name', 'item_code'])

        for item in items:
            if delivery_note.customer not in data_dict:
                data_dict[delivery_note.customer] = {'qty': 0, 'last_billing_date': delivery_note.posting_date, 'territory': delivery_note.territory, 'phone': ''}

            # Compute Total Qty Delivered
            data_dict[delivery_note.customer]['qty'] += item['qty']
            
            # Update last billing date
            if delivery_note.posting_date > data_dict[delivery_note.customer]['last_billing_date']:
                data_dict[delivery_note.customer]['last_billing_date'] = delivery_note.posting_date
            
            # Get phone number from linked address
            customer_address = frappe.get_all('Address', filters={'link_doctype': 'Customer', 'link_name': delivery_note.customer}, fields=['phone'])
            if customer_address:
                data_dict[delivery_note.customer]['phone'] = customer_address[0]['phone']

    # Prepare data for report
    data = []
    for customer, values in data_dict.items():
        data.append([customer, values['territory'], values['phone'], values['qty'], values['last_billing_date']])

    # Prepare columns for report
    columns = [
        'Customer:Link/Customer:360',
        'Territory:Data:120',
        'Phone:Data:120',
        'Total Qty Delivered:Float:180',
        'Last billing date:Date:180',

    ]

    return columns, data
