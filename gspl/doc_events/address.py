
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def before_save(doc, method):
    update_customer(doc)


def update_customer(doc):
    for dl in doc.links:
        if dl.link_doctype == "Customer":
            customer = frappe.get_doc(dl.link_doctype, dl.link_name)

            if doc.gstin:
                customer.gst_category = "Registered Regular"
                customer.territory = doc.gst_state

                if customer.territory == "West Bengal":
                    customer.tax_category = "In-State"
                else:
                    customer.tax_category = "Out-State"

                customer.save()

