
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def before_save(doc, method):
    update_content(doc)


def update_content(doc):

    if not doc.content:
        if doc.stock_uom == 'Meter':
            if doc.disabled:
                doc.content = 'Short Length'
            else:
                doc.content = 'Thaan'
        else:
            if doc.stock_uom == "Nos":
                doc.content = 'Combi'
                
