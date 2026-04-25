# sales_summary_document.py

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class SalesSummaryDocument(Document):
    def before_save(self):
        """
        Build Sales Summary Print Table entirely on the server,
        before every save—based on all linked Stock Entries.
        Rules:
          - item  = item_code
          - thaan = number of occurrences (row count) of that item across all Stock Entries
          - meter = sum of qty of that item across all Stock Entries
        """
        self._build_from_stock_entries()

    # ----- internal helpers -----
    def _build_from_stock_entries(self):
        # 1) Collect Stock Entry names from the child table
        se_names = [row.stock_entry for row in (self.stock_entry or []) if row.stock_entry]
        # If you want to enforce at least one SE, uncomment next line:
        # if not se_names: frappe.throw("Add at least one Stock Entry in the 'Stock Entry' table.")

        # 2) Aggregate occurrences and qty per item across all Stock Entries
        agg = {}  # item_code -> {"thaan": int, "meter": float}
        for se_name in se_names:
            try:
                se = frappe.get_doc("Stock Entry", se_name)
            except frappe.DoesNotExistError:
                # Skip missing/invalid links gracefully
                continue

            for d in (se.items or []):
                item_code = d.item_code
                if not item_code:
                    continue

                # ERPNext Stock Entry Detail has `qty`; use it as "meter".
                qty = flt(getattr(d, "qty", 0))
                if qty <= 0:
                    # ignore zero/negative quantities
                    continue

                bucket = agg.setdefault(item_code, {"thaan": 0, "meter": 0.0})
                bucket["thaan"] += 1          # count occurrence
                bucket["meter"] += qty        # sum qty

        # 3) Replace the print table with aggregated rows
        self.set("sales_summary_print_table", [])
        # sort by item for consistent display
        for item_code in sorted(agg.keys()):
            vals = agg[item_code]
            self.append("sales_summary_print_table", {
                "item": item_code,
                "thaan": int(vals["thaan"]),
                "meter": flt(vals["meter"], 3),
                # rate/amount intentionally left for Part 2
            })
