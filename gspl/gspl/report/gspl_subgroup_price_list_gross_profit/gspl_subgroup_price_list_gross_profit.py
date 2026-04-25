import frappe
from frappe import _

def execute(filters=None):
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    brand = filters.get("brand")
    type = filters.get("type")

    # Get all the sales invoices between the "from" and "to" dates
    invoices = frappe.get_all('Sales Invoice', filters={'posting_date': ['between', [from_date, to_date]]})

    # Get all selling price lists present in the system
    price_lists = frappe.get_all('Price List', filters={'selling': 1}, fields=['name'])
    price_list_names = [pl['name'] for pl in price_lists]

    # Create a dict with item_group as key and a dict of price lists as values
    data_dict = {}

    # Extract all the sales invoice items from these invoices
    for invoice in invoices:
        item_filters = {'parent': invoice.name}
        if brand:
            item_filters['brand'] = brand
        items = frappe.get_all('Sales Invoice Item', filters=item_filters, 
                               fields=['rate', 'price_list', 'item_group', 'qty', 'incoming_rate'])

        for item in items:
            # Get the item's price list
            price_list = item['price_list']

            if item['item_group'] not in data_dict:
                data_dict[item['item_group']] = {pl: {'numerator': 0, 'denominator': 0} for pl in price_list_names}
            
            if price_list in data_dict[item['item_group']]:
                data_dict[item['item_group']][price_list]['numerator'] += (item['rate'] - item['incoming_rate']) * item['qty']
                data_dict[item['item_group']][price_list]['denominator'] += item['rate'] * item['qty']

    # Prepare data for report
    data = []
    for item_group, price_lists in data_dict.items():
        row = [item_group]
        for pl in price_list_names:
            numerator = price_lists[pl]['numerator']
            denominator = price_lists[pl]['denominator']
            if type == "Percent":
                value = (numerator / denominator) * 100 if denominator != 0 else 0
            else:  # type == "Amount"
                value = numerator
            row.append(value)
        data.append(row)

    # Prepare columns for report
    column_type = 'Percent' if type == 'Percent' else 'Currency'
    columns = ['Item Group:Link/Item Group:120'] + [f'{pl}:{column_type}:120' for pl in price_list_names]

    return columns, data
