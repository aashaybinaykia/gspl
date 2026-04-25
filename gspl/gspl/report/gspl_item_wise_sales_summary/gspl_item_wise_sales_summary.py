import frappe
from frappe import _

def execute(filters=None):
    view = filters.get("view", "Item-wise")
    columns = get_columns(view)
    data = get_data(filters, view)
    return columns, data

def get_columns(view):
    if view == "Item-wise":
        return [
            {"fieldname": "item", "label": _("Item"), "fieldtype": "Link", "options": "Item", "width": 150},
            {"fieldname": "item_group", "label": _("Item Group"), "fieldtype": "Link", "options": "Item Group", "width": 150},
            {"fieldname": "brand", "label": _("Brand"), "fieldtype": "Link", "options": "Brand", "width": 150},
            {"fieldname": "total_qty", "label": _("Total Qty"), "fieldtype": "Float", "width": 100},
            {"fieldname": "total_delivered", "label": _("Total Delivered"), "fieldtype": "Int", "width": 100},
            {"fieldname": "available", "label": _("Available"), "fieldtype": "Int", "width": 100},
            {"fieldname": "pending_po", "label": _("Pending PO"), "fieldtype": "Float", "width": 110},  # NEW
            {"fieldname": "to_order", "label": _("To Order"), "fieldtype": "Float", "width": 100},
        ]
    elif view == "SO-wise-grouped":
        return [
            {"fieldname": "sales_order", "label": _("Sales Order"), "fieldtype": "Link", "options": "Sales Order", "width": 150},
            {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 150},
            {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
            {"fieldname": "qty", "label": _("Qty"), "fieldtype": "Float", "width": 100},
            {"fieldname": "delivered", "label": _("Delivered"), "fieldtype": "Int", "width": 100},
        ]
    else:
        return [
            {"fieldname": "sales_order", "label": _("Sales Order"), "fieldtype": "Link", "options": "Sales Order", "width": 150},
            {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Link", "options": "Customer", "width": 150},
            {"fieldname": "date", "label": _("Date"), "fieldtype": "Date", "width": 100},
            {"fieldname": "item", "label": _("Item"), "fieldtype": "Link", "options": "Item", "width": 150},
            {"fieldname": "item_group", "label": _("Item Group"), "fieldtype": "Link", "options": "Item Group", "width": 150},
            {"fieldname": "brand", "label": _("Brand"), "fieldtype": "Link", "options": "Brand", "width": 150},
            {"fieldname": "qty", "label": _("Qty"), "fieldtype": "Float", "width": 100},
            {"fieldname": "delivered", "label": _("Delivered"), "fieldtype": "Int", "width": 100},
            {"fieldname": "available", "label": _("Available"), "fieldtype": "Int", "width": 100},
            {"fieldname": "pending_po", "label": _("Pending PO"), "fieldtype": "Float", "width": 110},  # NEW
        ]

def get_data(filters, view):
    conditions = []

    if filters.get("from_date"):
        conditions.append("so.transaction_date >= %(from_date)s")
    if filters.get("to_date"):
        conditions.append("so.transaction_date <= %(to_date)s")
    if filters.get("sales_order"):
        conditions.append("so.name = %(sales_order)s")
    if filters.get("item"):
        conditions.append("soi.order_item = %(item)s")
    if filters.get("item_group"):
        conditions.append("i.item_group = %(item_group)s")
    if filters.get("brand"):
        conditions.append("i.brand = %(brand)s")
    if filters.get("content"):
        if filters.get("content") == "Loose":
            conditions.append("i.has_variants = 0")
        elif filters.get("content") == "Packed":
            conditions.append("i.has_variants = 1")

    conditions.append("so.status != 'Closed'")  # Exclude closed sales orders
    conditions_str = " AND ".join(conditions) if conditions else "1=1"

    if filters.get("content") == "Loose":
        available_query = """
            (
                SELECT COUNT(*)
                FROM `tabBatch` b
                WHERE b.item = soi.order_item
                  AND b.batch_qty > 5
            )
        """
        delivered_query = """
            (
                SELECT COUNT(*)
                FROM `tabDelivery Note Item` dni
                JOIN `tabDelivery Note` dn ON dn.name = dni.parent
                WHERE dni.item_code = soi.order_item
                  AND dni.against_sales_order = so.name
                  AND dn.docstatus = 1
                  AND dn.is_return = 0
            )
        """
        pending_po_query = """
            (
                SELECT COALESCE(SUM((poi.qty - poi.received_qty) / 10), 0)
                FROM `tabPurchase Order Item` poi
                JOIN `tabPurchase Order` po ON po.name = poi.parent
                WHERE poi.item_code = soi.order_item
                  AND po.docstatus < 2
                  AND po.status != 'Closed'
            )
        """
    else:  # content is "Packed"
        available_query = """
            (
                SELECT COUNT(*)
                FROM `tabCase Detail` cd
                JOIN `tabCase Detail Item Template` cdit ON cd.name = cdit.parent
                WHERE cd.status = 'Active'
                  AND cdit.item_template = soi.order_item
            )
        """
        delivered_query = """
            (
                SELECT COUNT(DISTINCT dni.case_detail)
                FROM `tabDelivery Note Item` dni
                JOIN `tabDelivery Note` dn ON dn.name = dni.parent
                JOIN `tabItem` i ON dni.item_code = i.name
                WHERE dni.against_sales_order = so.name
                  AND i.variant_of = soi.order_item
                  AND dn.docstatus = 1
                  AND dn.is_return = 0
            )
        """
        pending_po_query = """
            (
                SELECT COALESCE(SUM(poi.qty - poi.received_qty), 0)
                FROM `tabPurchase Order Item` poi
                JOIN `tabPurchase Order` po ON po.name = poi.parent
                JOIN `tabItem` vi ON vi.name = poi.item_code
                WHERE vi.variant_of = soi.order_item
                  AND po.docstatus = 1
                  AND po.status != 'Closed'
            )
        """

    if view == "Item-wise":
        query = """
            SELECT 
                soi.order_item as item,
                i.item_group,
                i.brand,
                SUM(soi.qty) as total_qty,
                SUM({delivered_query}) as total_delivered,
                {available_query} as available,
                {pending_po_query} as pending_po,
                (SUM(soi.qty) - SUM({delivered_query}) - {available_query} - {pending_po_query}) as to_order
            FROM 
                `tabSales Order` so
            JOIN 
                `tabSales Order Entry Item` soi ON so.name = soi.parent
            JOIN 
                `tabItem` i ON soi.order_item = i.name
            WHERE 
                so.docstatus < 2 AND {conditions}
            GROUP BY soi.order_item, i.item_group, i.brand
        """.format(
            delivered_query=delivered_query,
            available_query=available_query,
            pending_po_query=pending_po_query,
            conditions=conditions_str
        )
    elif view == "SO-wise-grouped":
        query = """
            SELECT 
                so.name as sales_order,
                so.customer,
                so.transaction_date as date,
                SUM(soi.qty) as qty,
                SUM({delivered_query}) as delivered
            FROM 
                `tabSales Order` so
            JOIN 
                `tabSales Order Entry Item` soi ON so.name = soi.parent
            JOIN 
                `tabItem` i ON soi.order_item = i.name
            WHERE 
                so.docstatus < 2 AND {conditions}
            GROUP BY so.name, so.customer, so.transaction_date
        """.format(
            delivered_query=delivered_query,
            conditions=conditions_str
        )
    else:
        query = """
            SELECT 
                so.name as sales_order,
                so.customer,
                so.transaction_date as date,
                soi.order_item as item,
                i.item_group,
                i.brand,
                soi.qty,
                {delivered_query} as delivered,
                {available_query} as available,
                {pending_po_query} as pending_po
            FROM 
                `tabSales Order` so
            JOIN 
                `tabSales Order Entry Item` soi ON so.name = soi.parent
            JOIN 
                `tabItem` i ON soi.order_item = i.name
            WHERE 
                so.docstatus < 2 AND {conditions}
        """.format(
            delivered_query=delivered_query,
            available_query=available_query,
            pending_po_query=pending_po_query,
            conditions=conditions_str
        )

    data = frappe.db.sql(query, filters, as_dict=True)
    return data
