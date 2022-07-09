
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def before_save(doc, method):
    calculate_rate_and_qty(doc)

def calculate_rate_and_qty(doc):
    total_rate = sum([row.rate for row in doc.items])
    total_qty = sum([row.qty for row in doc.items])

    doc.total_rate = total_rate
    doc.total_qty = total_qty
