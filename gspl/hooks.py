# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from . import __version__ as app_version

app_name = "gspl"
app_title = "GSPL"
app_publisher = "GSPL"
app_description = "GSPL"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@gspl.com"
app_license = "GPL 3.0"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/gspl/css/gspl.css"
# app_include_js = "/assets/gspl/js/gspl.js"

# include js, css files in header of web template
# web_include_css = "/assets/gspl/css/gspl.css"
# web_include_js = "/assets/gspl/js/gspl.js"

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "gspl.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "gspl.install.before_install"
# after_install = "gspl.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "gspl.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"gspl.tasks.all"
# 	],
# 	"daily": [
# 		"gspl.tasks.daily"
# 	],
# 	"hourly": [
# 		"gspl.tasks.hourly"
# 	],
# 	"weekly": [
# 		"gspl.tasks.weekly"
# 	]
# 	"monthly": [
# 		"gspl.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "gspl.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "gspl.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "gspl.task.get_dashboard_data
# }

doctype_js = {
	'Delivery Note': 'public/js/delivery_note.js',
	'Sales Order': 'public/js/sales_order.js',
	'Sales Invoice': 'public/js/sales_invoice.js',
	'Stock Entry': 'public/js/stock_entry.js',
}

override_whitelisted_methods = {
	"erpnext.selling.page.point_of_sale.point_of_sale.search_for_serial_or_batch_or_barcode_number": "gspl.overrides.whitelisted.point_of_sale.search_for_serial_or_batch_or_barcode_number",
	"erpnext.stock.doctype.batch.batch.get_batch_no": "gspl.overrides.whitelisted.batch.custom_get_batch_no",
	"erpnext.controllers.item_variant.create_variant":"gspl.overrides.whitelisted.item_variant.create_variant_override",
	"erpnext.controllers.item_variant.enqueue_multiple_variant_creation":"gspl.overrides.whitelisted.item_variant.enqueue_multiple_variant_creation_override",
}

override_doctype_class = {
    "Sales Invoice": "gspl.overrides.sales_invoice.CustomSalesInvoice",
}


# TODO: Uncomment and test below fixtures for TASK-17
fixtures = ["Custom Field", "Property Setter", "Client Script"]
# fixtures = [
# 	{
# 		"dt": "Custom Field",
# 		"filters": []
# 	},
# 	{
# 		"dt": "Client Script",
# 	},
# 	{
# 		"dt": "Property Setter",
# 		"filters": [("doc_type", "=", "Product Bundle Item")]
# 	}
# ]

doc_events = {
	"Address": {
		"before_save": "gspl.doc_events.address.before_save",
	},
	"Batch": {
		#"after_insert": "gspl.doc_events.batch.after_insert",
		# "on_trash": "gspl.doc_events.batch.on_trash",
	},
    "Delivery Note": {
		"on_submit": "gspl.doc_events.delivery_note.on_submit",
		"on_cancel": "gspl.doc_events.delivery_note.on_cancel",
		"validate": "gspl.doc_events.delivery_note.validate",
	},
	"Item": {
		"before_validate": "gspl.doc_events.item.before_validate",
	},
	"Case Detail": {
		"validate": "gspl.doc_events.case_detail.validate",
		"before_save": "gspl.doc_events.case_detail.before_save",
	},
	"Purchase Invoice": {
		"validate": "gspl.doc_events.purchase_invoice.validate",
		"on_submit": "gspl.doc_events.purchase_invoice.on_submit",
		"before_cancel": "gspl.doc_events.purchase_invoice.before_cancel",
	},
	# "Sales Order": {
	# 	"before_validate": "gspl.doc_events.sales_order.before_validate",
	# },
	# "Sales Invoice": {
	# 	"validate": "gspl.doc_events.sales_invoice.validate",
	# 	"before_save": "gspl.doc_events.sales_invoice.before_save",
	# 	"on_submit": "gspl.doc_events.sales_invoice.on_submit",
	# 	"on_cancel": "gspl.doc_events.sales_invoice.on_cancel",
	# },
	"Stock Entry": {
		"before_save": "gspl.doc_events.stock_entry.before_save",
		"before_submit": "gspl.doc_events.stock_entry.before_submit",
		"before_cancel": "gspl.doc_events.stock_entry.before_cancel",
	},
	"Stock Ledger Entry": {
		"validate": "gspl.doc_events.stock_ledger_entry.validate",
        "on_submit": "gspl.doc_events.stock_ledger_entry.on_submit",
	},
}
