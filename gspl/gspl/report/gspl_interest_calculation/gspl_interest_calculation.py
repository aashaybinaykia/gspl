import frappe
from frappe import _

def get_columns():
    return [
        {
            "label": _("Date"),
            "fieldname": "date",
            "fieldtype": "Date",
            "width": 100
        },
        {
            "label": _("Total Days"),
            "fieldname": "total_days",
            "fieldtype": "Int",
            "width": 100
        },
        {
            "label": _("Transaction Type"),
            "fieldname": "transaction_type",
            "width": 150
        },
        {
            "label": _("Amount"),
            "fieldname": "amount",
            "fieldtype": "Currency",
            "width": 300
        },
        {
            "label": _("Interest Amount"),
            "fieldname": "interest_amount",
            "fieldtype": "Currency",
            "width": 300
        }
    ]

def is_leap_year(year):
    """
    Check if the given year is a leap year.
    """
    if (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0):
        return True
    return False



def get_opening_balance(account, fiscal_year_start):
    # Query transactions
    transactions = frappe.get_all("GL Entry",
        filters={
            "account": account,
            "posting_date": ("<", fiscal_year_start),
            "is_cancelled": False  # Exclude cancelled transactions
        },
        fields=["debit", "credit"])

    # Calculate opening balance
    opening_balance = sum(entry.get("debit", 0) - entry.get("credit", 0) for entry in transactions)

    return opening_balance


def execute(filters=None):
    account = filters.get("account")
    fiscal_year = filters.get("fiscal_year")

    if not account or not fiscal_year:
        return get_columns(), []

    fiscal_year_start = frappe.db.get_value("Fiscal Year", fiscal_year, "year_start_date")
    fiscal_year_end = frappe.db.get_value("Fiscal Year", fiscal_year, "year_end_date")

    if not fiscal_year_start or not fiscal_year_end:
        frappe.throw(_("Fiscal year dates are not properly configured."))

    gl_entries = frappe.get_all("GL Entry", filters={
        "account": account, 
        "posting_date": ("between", [fiscal_year_start, fiscal_year_end]),
        "is_cancelled": False  # Only consider submitted GLEs
    }, fields=["posting_date", "debit", "credit"])

    account_doc = frappe.get_doc("Account", account)
    interest_rate = account_doc.interest/100

    total_interest_debit = 0
    div_days = 365
    total_interest_credit = 0
	
	# Check for leap year and adjust days outstanding accordingly
    if is_leap_year(fiscal_year_end.year):
    	div_days = 366
	

    interest_data = []
    opening = get_opening_balance(account,fiscal_year_start)
    opening_interest = opening * interest_rate 
    interest_data.append({
        "date": fiscal_year_start,
        "transaction_type": "Opening",
        "amount": opening,
        "interest_amount": opening_interest,
        "total_days": div_days  # Add total days field
    })
    for entry in gl_entries:
        # Calculate days outstanding
        days_outstanding = (fiscal_year_end - entry.posting_date).days
        days_outstanding += 1
	

        # Calculate interest amount
        interest_amount = 0

        # Determine transaction type
        if entry.debit:
            amount = entry.debit
            transaction_type = "Debit"
            interest_amount = (amount * interest_rate * days_outstanding) / div_days
            total_interest_debit += interest_amount
        else:
            amount = -entry.credit
            transaction_type = "Credit"
            interest_amount = (amount * interest_rate * days_outstanding) / div_days
            total_interest_credit += interest_amount
        
        # Calculate interest amount
        interest_amount = (amount * interest_rate * days_outstanding) / div_days
        
        # Append data to interest_data list
        interest_data.append({
            "date": entry.posting_date,
            "transaction_type": transaction_type,
            "amount": amount,
            "interest_amount": interest_amount,
            "total_days": days_outstanding  # Add total days field
        })

    # Calculate net interest amount and determine transaction type
    net_interest_amount = abs(total_interest_debit - total_interest_credit)
    if total_interest_debit > total_interest_credit:
        final_transaction_type = "Debit"
    else:
        final_transaction_type = "Credit"

    # Add a final row with the net interest amount and transaction type
    # interest_data.append({
    #     "date": fiscal_year_end,
    #     "transaction_type": final_transaction_type,
    #     "amount": 0,
    #     "interest_amount": net_interest_amount,
    #     "total_days": 0  # Total days for final row can be 0 or calculated differently if needed
    # })
    sorted_interest_data = sorted(interest_data, key=lambda x: x['date'])
    return get_columns(), sorted_interest_data
