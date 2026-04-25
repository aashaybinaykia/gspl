import frappe
from frappe.utils import flt, today, getdate
from datetime import datetime

def execute(filters=None):
	if not filters:
		filters = {}

	from_date = filters.get("from_date") or "1900-01-01"
	to_date = filters.get("to_date") or today()
	from_date_date = datetime.strptime(from_date, "%Y-%m-%d").date()
	to_date_date = datetime.strptime(to_date, "%Y-%m-%d").date()
	today_date = getdate()

	columns = [
		{"label": "Customer", "fieldname": "customer", "fieldtype": "Link", "options": "Customer", "width": 180},
		{"label": "Total", "fieldname": "total_invoiced", "fieldtype": "Currency", "width": 120},
		{"label": "Total Payment Received", "fieldname": "total_paid", "fieldtype": "Currency", "width": 150},
		{"label": "Outstanding Amount", "fieldname": "outstanding", "fieldtype": "Currency", "width": 150},
		{"label": "Last Billed Date", "fieldname": "last_billed", "fieldtype": "Date", "width": 120},
		{"label": "Last Payment Received", "fieldname": "last_payment", "fieldtype": "Date", "width": 150},
		{"label": "Weighted Avg Payment Days", "fieldname": "avg_payment_days", "fieldtype": "Data", "width": 150}
	]

	# === Filters for customer-level filtering ===
	customer_filter_clause = ""
	if filters.get("customer"):
		customer_filter_clause += f" AND gle.party = '{filters['customer']}'"
	if filters.get("sales_partner"):
		customer_filter_clause += f" AND c.default_sales_partner = '{filters['sales_partner']}'"
	if filters.get("customer_group"):
		customer_filter_clause += f" AND c.customer_group = '{filters['customer_group']}'"
	if filters.get("territory"):
		customer_filter_clause += f" AND c.territory = '{filters['territory']}'"
	if filters.get("sales_manager"):
		customer_filter_clause += f" AND c.sales_manager = '{filters['sales_manager']}'"
	if filters.get("customer_grade") == "A":
		customer_filter_clause += f" AND c.customer_grade = 'A'"
	elif filters.get("customer_grade") == "Others":
		customer_filter_clause += f" AND (c.customer_grade != 'A' OR c.customer_grade IS NULL)"

	# === Get active customers with GL activity matching filters ===
	customers = frappe.db.sql(f"""
		SELECT DISTINCT gle.party
		FROM `tabGL Entry` gle
		LEFT JOIN `tabCustomer` c ON gle.party = c.name
		WHERE gle.docstatus = 1 AND gle.party_type = 'Customer' AND gle.party IS NOT NULL
		{customer_filter_clause}
	""", as_dict=True)

	customer_list = [c.party for c in customers]

	# === Get total invoiced (with date filter) ===
	total_invoiced_map = {}
	last_billed_map = {}
	invoice_rows = frappe.db.sql("""
		SELECT 
			customer AS party,
			SUM(base_grand_total) AS total_invoiced,
			(
				SELECT MAX(posting_date)
				FROM `tabSales Invoice` si2
				WHERE si2.customer = si.customer AND si2.docstatus = 1 AND si2.is_return = 0
			) AS last_billed
		FROM `tabSales Invoice` si
		WHERE docstatus = 1 
		AND posting_date BETWEEN %s AND %s
		GROUP BY customer
	""", (from_date_date, to_date_date), as_dict=True)
	# === Store values in map
	for row in invoice_rows:
		total_invoiced_map[row.party] = flt(row.total_invoiced)
		last_billed_map[row.party] = row.last_billed

	# === Payment Received (within filter dates only)
	period_payment_map = {}
	for row in frappe.db.sql("""
		SELECT party AS customer, SUM(paid_amount) AS total_pe
		FROM `tabPayment Entry`
		WHERE party_type = 'Customer' AND docstatus = 1 AND posting_date BETWEEN %s AND %s
		GROUP BY party
	""", (from_date_date, to_date_date), as_dict=True):
		period_payment_map[row.customer] = flt(row.total_pe)

	for row in frappe.db.sql("""
		SELECT jea.party AS customer, SUM(jea.credit_in_account_currency - jea.debit_in_account_currency) AS total_je
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE je.docstatus = 1 AND jea.party_type = 'Customer' AND je.posting_date BETWEEN %s AND %s
		GROUP BY jea.party
	""", (from_date_date, to_date_date), as_dict=True):
		period_payment_map[row.customer] = period_payment_map.get(row.customer, 0.0) + flt(row.total_je)

	# === Last Payment Date
	payment_map = {}
	for row in frappe.db.sql("""
		SELECT party AS customer, MAX(posting_date) AS last_pe
		FROM `tabPayment Entry`
		WHERE party_type = 'Customer' AND docstatus = 1
		GROUP BY party
	""", as_dict=True):
		payment_map[row.customer] = {"last_payment": row.last_pe}

	for row in frappe.db.sql("""
		SELECT jea.party AS customer, MAX(je.posting_date) AS last_je
		FROM `tabJournal Entry Account` jea
		JOIN `tabJournal Entry` je ON je.name = jea.parent
		WHERE jea.party_type = 'Customer' AND je.docstatus = 1
		GROUP BY jea.party
	""", as_dict=True):
		if row.customer in payment_map:
			payment_map[row.customer]["last_payment"] = max(payment_map[row.customer]["last_payment"], row.last_je)
		else:
			payment_map[row.customer] = {"last_payment": row.last_je}

	# === FIFO from GL for all customers
	invoice_detail_map = {}
	payment_map_fifo = {}
	gl_entries = frappe.db.sql("""
		SELECT posting_date, party, debit, credit
		FROM `tabGL Entry`
		WHERE party_type = 'Customer' AND docstatus = 1 AND party IS NOT NULL
		ORDER BY posting_date ASC
	""", as_dict=True)

	for row in gl_entries:
		customer = row.party
		posting_date = row.posting_date.date() if isinstance(row.posting_date, datetime) else row.posting_date

		if flt(row.debit) > 0 and posting_date <= to_date_date:
			invoice_detail_map.setdefault(customer, []).append({"amount": flt(row.debit), "posting_date": posting_date})
		elif flt(row.credit) > 0:
			payment_map_fifo.setdefault(customer, []).append({"amount": flt(row.credit), "posting_date": posting_date})

	avg_days_map = {}
	outstanding_map = {}

	for customer in customer_list:
		invoices = invoice_detail_map.get(customer, [])
		payments = [p.copy() for p in payment_map_fifo.get(customer, [])]
		i = j = 0
		customer_matches = []

		while i < len(invoices) and j < len(payments):
			inv = invoices[i]
			pay = payments[j]

			if inv["amount"] == 0:
				i += 1
				continue
			if pay["amount"] == 0:
				j += 1
				continue

			alloc = min(inv["amount"], pay["amount"])
			invoice_date = inv["posting_date"]
			cleared_on = pay["posting_date"]
			delay = (cleared_on - invoice_date).days

			customer_matches.append({
				"invoice_date": invoice_date,
				"cleared_on": cleared_on,
				"allocated_amount": alloc,
				"delay_days": delay
			})

			inv["amount"] -= alloc
			pay["amount"] -= alloc

		# Step 1: Efficiently compute max delay from actually paid invoices
		max_paid_delay = 0
		for entry in customer_matches:
			if entry["cleared_on"] != today_date:
				max_paid_delay = max(max_paid_delay, entry["delay_days"])

		# Step 2: Add remaining unpaid/partially paid invoices
		for inv in invoices:
			if inv["amount"] > 0 and inv["posting_date"] <= to_date_date:
				delay = (today_date - inv["posting_date"]).days
				# Adjust unpaid delay if it's shorter than any paid delay
				if delay < max_paid_delay:
					delay = max_paid_delay
				customer_matches.append({
					"invoice_date": inv["posting_date"],
					"cleared_on": today_date,
					"allocated_amount": inv["amount"],
					"delay_days": delay
				})


		filtered_matches = [entry for entry in customer_matches if entry["cleared_on"] >= from_date_date and entry["invoice_date"] <= to_date_date]

		if filtered_matches:
			total_days = sum(entry["delay_days"] * entry["allocated_amount"] for entry in filtered_matches)
			total_amt = sum(entry["allocated_amount"] for entry in filtered_matches)
			avg_days_map[customer] = round(total_days / total_amt, 1) if total_amt else "No Payment Received"
		else:
			avg_days_map[customer] = "No Payment Received"

		outstanding_map[customer] = sum(inv["amount"] for inv in invoices if inv["posting_date"] <= to_date_date)

	# === Final Data Assembly
	final_data = []
	for customer in customer_list:
		final_data.append({
			"customer": customer,
			"total_invoiced": flt(total_invoiced_map.get(customer, 0.0)),
			"total_paid": flt(period_payment_map.get(customer, 0.0)),
			"outstanding": flt(outstanding_map.get(customer, 0.0)),
			"last_billed": last_billed_map.get(customer),
			"last_payment": payment_map.get(customer, {}).get("last_payment"),
			"avg_payment_days": avg_days_map.get(customer)
		})

	# === Weighted Avg Row
	# Weighted Average (using total_invoiced + outstanding)
	weighted_num = sum(
		(row["total_invoiced"] + row["outstanding"]) * row["avg_payment_days"]
		for row in final_data
		if isinstance(row["avg_payment_days"], (int, float))
	)
	weighted_den = sum(
		row["total_invoiced"] + row["outstanding"]
		for row in final_data
		if isinstance(row["avg_payment_days"], (int, float))
	)
	weighted_avg = round(weighted_num / weighted_den, 1) if weighted_den else "N/A"

	# Simple Average
	simple_values = [row["avg_payment_days"] for row in final_data if isinstance(row["avg_payment_days"], (int, float))]
	simple_avg = round(sum(simple_values) / len(simple_values), 1) if simple_values else "N/A"

	# Sort by customer name, but place summary row later
	final_data.sort(key=lambda x: x["customer"] if isinstance(x["customer"], str) else "ZZZ")

	# Final row
	final_data.append({
		"customer": "🔹 Summary",
		"total_invoiced": "—",
		"total_paid": "—",
		"outstanding": "—",
		"last_billed": "",
		"last_payment": "",
    	"avg_payment_days": f"Weighted: {weighted_avg}, Avg: {simple_avg}"
	})


	return columns, final_data
