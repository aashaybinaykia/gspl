# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

import frappe
from frappe import _, scrub

import erpnext.accounts.party
from erpnext.accounts.report.accounts_receivable_summary.accounts_receivable_summary import AccountsReceivableSummary

# --- BUGFIX PATCH FOR ERPNEXT v16 ---
# ERPNext v16 has a known bug where passing a string to get_partywise_advanced_payment_amount 
# causes PyPika's .isin() to crash. This patch intercepts the call and ensures it is safely passed as a list.
_original_get_advances = erpnext.accounts.party.get_partywise_advanced_payment_amount

def _patched_get_advances(*args, **kwargs):
	args_list = list(args)
	# If the first argument (party_type) is a string, wrap it in a list
	if len(args_list) > 0 and isinstance(args_list[0], str):
		args_list[0] = [args_list[0]]
	# Also check keyword arguments just in case
	if "party_type" in kwargs and isinstance(kwargs["party_type"], str):
		kwargs["party_type"] = [kwargs["party_type"]]
	return _original_get_advances(*args_list, **kwargs)

# Apply the patch globally for this report execution
erpnext.accounts.party.get_partywise_advanced_payment_amount = _patched_get_advances
# ------------------------------------


def execute(filters=None):
	args = {
		"party_type": "Customer", # Kept as a string so ReceivablePayableReport works
		"naming_by": ["Selling Settings", "cust_master_name"],
	}
	return GSPLAccountsReceivableSummary(filters).run(args)


class GSPLAccountsReceivableSummary(AccountsReceivableSummary):
	def get_columns(self):
		self.columns = []

		if self.party_type == "Customer":
			self.add_column(
				label=_(self.party_type + " Link"),
				fieldname="party_link",
				fieldtype="HTML",
				width=180,
			)
		
		self.add_column(label=_("Sales Partner"), fieldname="sales_partner", fieldtype="Link", options="Sales Partner")

		if getattr(self, "party_naming_by", None) == "Naming Series":
			self.add_column(_("{0} Name").format(self.party_type), fieldname="party_name", fieldtype="Data")

		self.add_column(_("Outstanding Amount"), fieldname="outstanding")

		if self.filters.get("show_gl_balance"):
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
			if self.filters.get("show_sales_person"):
				self.add_column(label=_("Sales Person"), fieldname="sales_person", fieldtype="Data")

		else:
			self.add_column(
				label=_("Supplier Group"),
				fieldname="supplier_group",
				fieldtype="Link",
				options="Supplier Group",
			)

	def get_data(self, args):
		# Ensure self.party_type is set properly as a string for ReceivablePayableReport
		self.party_type = args.get("party_type", "Customer")
		
		if hasattr(self, "filters") and self.filters:
			self.filters.party_type = self.party_type
		elif not hasattr(self, "filters"):
			self.filters = frappe._dict({"party_type": self.party_type})

		# Call standard core code (patched above to prevent the PyPika crash)
		super().get_data(args)

		if self.party_type == "Customer":
			for row in self.data:
				row.party_link = f"""<a href="/app/query-report/Accounts%20Receivable?company=Gautam%20Syntex%20Pvt%20Ltd&report_date=2023-06-26&customer={row.party}&ageing_based_on=Posting%20Date&range1=90&range2=180&range3=360&range4=720&customer_name=DHANLAXMI%20-%20FORBESGANJ&payment_terms=75" target="_blank">{row.party}</a>"""
				row.sales_partner = frappe.db.get_value("Customer", row.party, "default_sales_partner")