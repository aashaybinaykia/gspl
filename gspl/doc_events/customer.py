
from __future__ import unicode_literals

import frappe
from frappe import _


@frappe.whitelist()
def before_validate(doc, method):
	if doc.mobile_no:
		doc.phone = doc.mobile_no
		doc.mobile_no = None
	if not doc.phone:
		frappe.throw("Mobile No Is Cumpolsory")
                
