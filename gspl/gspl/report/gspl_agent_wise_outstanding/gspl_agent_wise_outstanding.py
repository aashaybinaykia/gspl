import frappe
from frappe import _

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"fieldname": "agent", "label": _("Agent"), "fieldtype": "Data", "width": 150},
        {"fieldname": "customer", "label": _("Customer"), "fieldtype": "Data", "width": 200},
        {"fieldname": "posting_date", "label": _("DATE"), "fieldtype": "Date", "width": 110},
        {"fieldname": "voucher_no", "label": _("SR. NO."), "fieldtype": "Data", "width": 120},
        {"fieldname": "amount", "label": _("AMOUNT."), "fieldtype": "Currency", "width": 120},
        {"fieldname": "dr_cr", "label": _("DrCr"), "fieldtype": "Data", "width": 60},
        {"fieldname": "outstanding_amount", "label": _("BAL. AMT."), "fieldtype": "Currency", "width": 120}
    ]

def get_data(filters):
    # 1. Fetch raw balances from GL Entry grouped by voucher
    conditions = "gl.party_type = 'Customer' AND gl.is_cancelled = 0"
    if filters.get("to_date"):
        conditions += f" AND gl.posting_date <= '{filters.get('to_date')}'"
        
    sql = f"""
        SELECT
            IFNULL(si.sales_partner, IFNULL(c.default_sales_partner, 'No Agent Linked')) as agent,
            gl.party as customer,
            MIN(gl.posting_date) as posting_date,
            IFNULL(gl.against_voucher, gl.voucher_no) as voucher_no,
            SUM(gl.debit) as original_debit,
            SUM(gl.credit) as original_credit,
            SUM(gl.debit - gl.credit) as outstanding_amount
        FROM
            `tabGL Entry` gl
        JOIN 
            `tabCustomer` c ON gl.party = c.name
        LEFT JOIN 
            `tabSales Invoice` si ON IFNULL(gl.against_voucher, gl.voucher_no) = si.name 
            AND (gl.against_voucher_type = 'Sales Invoice' OR gl.voucher_type = 'Sales Invoice')
        WHERE
            {conditions}
        GROUP BY
            gl.party, IFNULL(gl.against_voucher, gl.voucher_no)
        HAVING
            ROUND(SUM(gl.debit - gl.credit), 2) != 0
        ORDER BY
            posting_date ASC
    """
    raw_data = frappe.db.sql(sql, as_dict=True)

    # 2. Group by Customer to prepare for FIFO
    customer_records = {}
    for row in raw_data:
        cust = row.customer
        if cust not in customer_records:
            customer_records[cust] = {'invoices': [], 'credits': []}
        
        # Determine the original transaction value for the report
        row.amount = row.original_debit if row.original_debit > 0 else row.original_credit
        
        if row.outstanding_amount > 0:
            customer_records[cust]['invoices'].append(row)
        else:
            # Store the unlinked credit as a positive number for easy math
            row.unallocated_credit = abs(row.outstanding_amount)
            customer_records[cust]['credits'].append(row)

    # 3. Apply the Virtual FIFO Allocation
    final_data = []
    
    for cust, records in customer_records.items():
        # Ensure invoices are sorted oldest to newest
        invoices = sorted(records['invoices'], key=lambda x: x.posting_date)
        
        # Pool all unallocated credits together for this customer
        total_unallocated = sum(c.unallocated_credit for c in records['credits'])
        
        # Apply the credit pool to the invoices sequentially
        for inv in invoices:
            if total_unallocated <= 0:
                break # No more credit to apply
            
            if total_unallocated >= inv.outstanding_amount:
                # Credit covers the whole invoice; zero it out and reduce the pool
                total_unallocated -= inv.outstanding_amount
                inv.outstanding_amount = 0
            else:
                # Credit partially covers the invoice
                inv.outstanding_amount -= total_unallocated
                total_unallocated = 0
                
        # 4. Save the surviving invoices that still have a balance
        for inv in invoices:
            if round(inv.outstanding_amount, 2) > 0:
                inv.dr_cr = "D"
                final_data.append(inv)
                
        # 5. If there is still credit leftover after all invoices are paid, show it as an Advance
        if round(total_unallocated, 2) > 0:
            # Find the correct agent to assign this advance to
            agent_val = invoices[0].agent if invoices else (records['credits'][0].agent if records['credits'] else "No Agent Linked")
            
            final_data.append(frappe._dict({
                "agent": agent_val,
                "customer": cust,
                "posting_date": records['credits'][-1].posting_date if records['credits'] else None,
                "voucher_no": "Unallocated Advance",
                "amount": total_unallocated,
                "outstanding_amount": -abs(total_unallocated), # Keep negative so HTML prints 'C'
                "dr_cr": "C"
            }))

    # 6. Apply the Agent Filter (Done after FIFO so generic advances still pay off the agent's invoices)
    agent_filter = filters.get("sales_partner")
    if agent_filter:
        final_data = [d for d in final_data if d.agent == agent_filter]

    # 7. Final sort for clean grouping on the print format
    final_data = sorted(final_data, key=lambda x: (x.agent, x.customer, x.posting_date))
    
    return final_data