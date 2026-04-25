import frappe
from frappe.utils import flt, getdate
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict, OrderedDict

MONTH_ORDER = {
    'Apr': 4, 'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8, 'Sep': 9,
    'Oct': 10, 'Nov': 11, 'Dec': 12, 'Jan': 1, 'Feb': 2, 'Mar': 3
}


def execute(filters=None):
    if not filters:
        filters = {}

    group_by = filters.get("group_by", "Customer")
    metric = filters.get("metric", "Amount")
    periodicity = filters.get("periodicity", "Monthly")
    from_date = getdate(filters["from_date"])
    to_date = getdate(filters["to_date"])

    period_list = get_periods(from_date, to_date, periodicity)
    customers = get_filtered_customers(filters)
    items = get_filtered_items(filters)
    data = get_sales_data(customers, items, from_date, to_date, group_by, metric, period_list, periodicity, filters)

    link_map = {
        "Customer": "Customer",
        "Item": "Item",
        "Item Template": "Item",
        "Item Group": "Item Group",
        "Brand": "Brand",
        "Sales Partner": "Sales Partner",
        "Customer Group": "Customer Group",
        "Territory": "Territory",
        "Sales Manager": "Sales Person"
    }

    columns = [{
        "label": group_by,
        "fieldname": "group",
        "fieldtype": "Link" if group_by in link_map else "Data",
        "options": link_map.get(group_by),
        "width": 200
    }]
    value_fieldtype = "Currency" if metric == "Amount" else "Float"
    for period in period_list:
        columns.append({
            "label": period,
            "fieldname": period,
            "fieldtype": value_fieldtype,
            "width": 120
        })
    columns.append({
        "label": "Total",
        "fieldname": "total",
        "fieldtype": value_fieldtype,
        "width": 120
    })

    # Modified logic to ensure all customers are included (with zero values if no data)
    result = []
    all_groups = set(data.keys())

    if group_by == "Customer":
        all_groups.update(customers)  # Ensure every filtered customer is represented

    for group_key in sorted(k for k in all_groups if k is not None):
        row = {"group": group_key}
        total = 0
        for period in period_list:
            value = flt(data.get(group_key, {}).get(period, 0))
            row[period] = value
            total += value
        row["total"] = total
        result.append(row)

    if None in data:
        row = {"group": "Unknown"}
        total = 0
        for period in period_list:
            value = flt(data[None].get(period))
            row[period] = value
            total += value
        row["total"] = total
        result.append(row)

    return columns, result

# (rest of the code remains unchanged)



def get_filtered_customers(filters):
    conditions = ["is_frozen = 0"]
    values = {}

    if filters.get("customer"):
        return [filters["customer"]]

    if filters.get("sales_partner"):
        conditions.append("default_sales_partner = %(sales_partner)s")
        values["sales_partner"] = filters["sales_partner"]
    if filters.get("customer_group"):
        conditions.append("customer_group = %(customer_group)s")
        values["customer_group"] = filters["customer_group"]
    if filters.get("territory"):
        conditions.append("territory = %(territory)s")
        values["territory"] = filters["territory"]
    if filters.get("sales_manager"):
        conditions.append("sales_manager = %(sales_manager)s")
        values["sales_manager"] = filters["sales_manager"]
    if filters.get("grade"):
        conditions.append("grade = %(grade)s")
        values["grade"] = filters["grade"]
    if filters.get("region"):
        conditions.append("region LIKE %(region)s")
        values["region"] = f"%{filters['region']}%"
    if filters.get("division"):
        conditions.append("division LIKE %(division)s")
        values["division"] = f"%{filters['division']}%"
    if filters.get("area"):
        conditions.append("area LIKE %(area)s")
        values["area"] = f"%{filters['area']}%"

    condition_str = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return [d.name for d in frappe.db.sql(f"SELECT name FROM `tabCustomer` {condition_str}", values, as_dict=True)]


def get_filtered_items(filters):
    conditions = []
    values = {}

    if filters.get("item"):
        return [filters["item"]]

    if filters.get("item_group"):
        conditions.append("item_group = %(item_group)s")
        values["item_group"] = filters["item_group"]
    if filters.get("brand"):
        conditions.append("brand = %(brand)s")
        values["brand"] = filters["brand"]
    if filters.get("variant_of"):
        conditions.append("variant_of = %(variant_of)s")
        values["variant_of"] = filters["variant_of"]

    condition_str = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    return [d.name for d in frappe.db.sql(f"SELECT name FROM `tabItem` {condition_str}", values, as_dict=True)]


def get_periods(from_date, to_date, periodicity):
    period_entries = []
    current = from_date.replace(day=1)

    while current <= to_date:
        fy = current.year if current.month >= 4 else current.year - 1
        fy_label = f"FY {fy}-{str(fy + 1)[-2:]}"

        if periodicity == "Monthly":
            sub_period = current.strftime("%b")
            full_label = f"{sub_period} {fy_label}"
            month_number = MONTH_ORDER[sub_period]
            period_entries.append((month_number, fy, full_label))
            current += relativedelta(months=1)

        elif periodicity == "Quarterly":
            quarter = ((current.month - 4) % 12) // 3 + 1
            sub_period = f"Q{quarter}"
            full_label = f"{sub_period} {fy_label}"
            period_entries.append((quarter, fy, full_label))
            current += relativedelta(months=3)

        elif periodicity == "Half-Yearly":
            half = 1 if 4 <= current.month <= 9 else 2
            sub_period = f"H{half}"
            full_label = f"{sub_period} {fy_label}"
            period_entries.append((half, fy, full_label))
            current += relativedelta(months=6)

        elif periodicity == "Yearly":
            full_label = fy_label
            period_entries.append((0, fy, full_label))
            current += relativedelta(years=1)

    return [label for _, _, label in sorted(period_entries)]


def get_period_label(date, periodicity):
    fy = date.year if date.month >= 4 else date.year - 1
    fy_label = f"FY {fy}-{str(fy + 1)[-2:]}"

    if periodicity == "Monthly":
        return f"{date.strftime('%b')} {fy_label}"
    elif periodicity == "Quarterly":
        quarter = ((date.month - 4) % 12) // 3 + 1
        return f"Q{quarter} {fy_label}"
    elif periodicity == "Half-Yearly":
        half = 1 if 4 <= date.month <= 9 else 2
        return f"H{half} {fy_label}"
    elif periodicity == "Yearly":
        return fy_label
    return ""


def get_sales_data(customers, items, from_date, to_date, group_by, metric, period_list, periodicity,filters):
    value_field = "sii.base_net_amount" if metric == "Amount" else "sii.qty"

    group_field_map = {
        "Customer": "si.customer",
        "Item": "sii.item_code",
        "Item Template": "i.variant_of",
        "Item Group": "i.item_group",
        "Brand": "i.brand",
        "Sales Partner": "c.sales_partner",
        "Customer Group": "c.customer_group",
        "Territory": "c.territory",
        "Sales Manager": "c.sales_manager",
        "Grade": "c.grade",
        "Content": "dnti.content",
        "Region": "c.region",
        "Division": "c.division",
        "Area": "c.area",

    }

    group_field = group_field_map.get(group_by, "si.customer")

    filters_dict = {
        "from_date": from_date,
        "to_date": to_date,
        "items": items,
        "customers": customers
    }

    conditions = ""
    if items:
        conditions += " AND sii.item_code IN %(items)s"
    if customers:
        conditions += " AND si.customer IN %(customers)s"

    # Content filter from Delivery Note Item
    content_condition = ""
    if filters.get("content"):
        content_condition = " AND dnti.content = %(content)s"
        filters_dict["content"] = filters["content"]

    sql = f"""
        SELECT
            {group_field} AS group_key,
            si.posting_date,
            {value_field} AS value
        FROM
            `tabSales Invoice Item` sii
        JOIN
            `tabSales Invoice` si ON si.name = sii.parent
        JOIN
            `tabItem` i ON i.name = sii.item_code
        JOIN
            `tabCustomer` c ON c.name = si.customer
        LEFT JOIN
            `tabDelivery Note Item` dnti ON dnti.name = sii.dn_detail
        WHERE
            si.docstatus = 1
            AND si.posting_date BETWEEN %(from_date)s AND %(to_date)s
            {conditions}
            {content_condition}
    """

    results = frappe.db.sql(sql, filters_dict, as_dict=True)
    data = defaultdict(lambda: defaultdict(float))

    for row in results:
        period_label = get_period_label(row.posting_date, periodicity)
        if period_label in period_list:
            data[row.group_key][period_label] += flt(row.value)

    return data

