# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub
from frappe.utils import cint, flt

from erpnext.accounts.party import get_partywise_advanced_payment_amount
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import AccountsReceivableSummary


def execute(filters=None):
	args = {
		"party_type": "Customer",
		"naming_by": ["Selling Settings", "cust_master_name"],
	}

	return GSPLAccountsReceivableSummary(filters).run(args)


class GSPLAccountsReceivableSummary(AccountsReceivableSummary):
	def get_columns(self):
		self.columns = []
		# self.add_column(
		# 	label=_(self.party_type),
		# 	fieldname="party",
		# 	fieldtype="Link",
		# 	options=self.party_type,
		# 	width=180,
		# )


		if self.party_type == "Customer":
			self.add_column(
				label=_(self.party_type + " Link"),
				fieldname="party_link",
				fieldtype="HTML",
				width=180,
			)
		

		self.add_column(label=_("Sales Partner"), fieldname="sales_partner", fieldtype="Link", options= "Sales Partner")

		if self.party_naming_by == "Naming Series":
			self.add_column(_("{0} Name").format(self.party_type), fieldname="party_name", fieldtype="Data")


		self.add_column(_("Outstanding Amount"), fieldname="outstanding")

		if self.filters.show_gl_balance:
			self.add_column(_("GL Balance"), fieldname="gl_balance")
			self.add_column(_("Difference"), fieldname="diff")

		self.setup_ageing_columns()

		if self.party_type == "Customer":
			self.add_column(
				label=_("Territory"), fieldname="territory", fieldtype="Link", options="Territory"
			)
			self.add_column(
				label=_("Customer Group"),
				fieldname="customer_group",
				fieldtype="Link",
				options="Customer Group",
			)
			if self.filters.show_sales_person:
				self.add_column(label=_("Sales Person"), fieldname="sales_person", fieldtype="Data")



		else:
			self.add_column(
				label=_("Supplier Group"),
				fieldname="supplier_group",
				fieldtype="Link",
				options="Supplier Group",
			)



	def get_data(self, args):
		super().get_data(args)

		if self.party_type == "Customer":
			for row in self.data:
				row.party_link = f"""<a href="/app/query-report/Accounts%20Receivable?company=Gautam%20Syntex%20Pvt%20Ltd&report_date=2023-06-26&customer={row.party}&ageing_based_on=Posting%20Date&range1=90&range2=180&range3=360&range4=720&customer_name=DHANLAXMI%20-%20FORBESGANJ&payment_terms=75" target="_blank">{row.party}</a>"""
				row.sales_partner =  frappe.db.get_value("Customer", row.party, "default_sales_partner")