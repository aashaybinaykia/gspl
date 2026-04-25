# sales_summary_document.py

import frappe
from frappe.model.document import Document
from frappe.utils import flt

class SalesSummaryDocument(Document):
    def before_save(self):
        """
        Build Sales Summary Print Table in this order:
          1) Items from Stock Entries (Part 1 logic)
          2) Items from Case Detail Transfers (Part 2 logic)
        Then:
          - Preserve existing per-item rates from current table
          - If no direct rate, use template (variant_of) rate if available
          - Compute amount = meter * rate whenever rate is present
          - Add a TOTAL row at the end
        """

        # Dedupe child link rows so UI reflects true state
        self._dedupe_child_links("stock_entry", "stock_entry")
        self._dedupe_child_links("case_details_transfer", "case_detail_transfer")

        # --- Aggregate data ---
        stock_entry_data = self._aggregate_from_stock_entries()
        case_detail_data = self._aggregate_from_case_details()

        # --- Preserve existing rates ---
        existing_rates = {}
        for r in (self.sales_summary_print_table or []):
            item = (getattr(r, "item", "") or "").strip()
            rate = flt(getattr(r, "rate", 0))
            if item and rate:
                existing_rates.setdefault(item, rate)

        # --- Template-based rate fallback ---
        def _get_template(item_code: str) -> str:
            variant_of = frappe.get_cached_value("Item", item_code, "variant_of")
            return variant_of or item_code

        template_rates = {}
        for item_code, rate in existing_rates.items():
            if not rate:
                continue
            tmpl = _get_template(item_code)
            template_rates.setdefault(tmpl, rate)

        # --- Build final print table (Stock Entries first, then Case Details) ---
        self.set("sales_summary_print_table", [])
        total_thaan = total_meter = total_amount = 0.0

        # 1️⃣ Stock Entry items first
        for item_code in sorted(stock_entry_data.keys()):
            vals = stock_entry_data[item_code]
            meter = flt(vals["meter"], 3)
            thaan = int(vals["thaan"])

            rate = flt(existing_rates.get(item_code, 0))
            if not rate:
                tmpl = _get_template(item_code)
                rate = flt(template_rates.get(tmpl, 0))
            amount = meter * rate if rate else 0

            self.append("sales_summary_print_table", {
                "item": item_code,
                "thaan": thaan,
                "meter": meter,
                "rate": rate if rate else None,
                "amount": flt(amount, 2) if rate else None,
            })

            total_thaan += thaan
            total_meter += meter
            total_amount += amount

        # 2️⃣ Case Detail Transfer items next
        for item_code in sorted(case_detail_data.keys()):
            vals = case_detail_data[item_code]
            meter = flt(vals["meter"], 3)
            thaan = int(vals["thaan"])

            rate = flt(existing_rates.get(item_code, 0))
            if not rate:
                tmpl = _get_template(item_code)
                rate = flt(template_rates.get(tmpl, 0))
            amount = meter * rate if rate else 0

            self.append("sales_summary_print_table", {
                "item": item_code,
                "thaan": thaan,
                "meter": meter,
                "rate": rate if rate else None,
                "amount": flt(amount, 2) if rate else None,
            })

            total_thaan += thaan
            total_meter += meter
            total_amount += amount

        # 3️⃣ TOTAL row
        self.append("sales_summary_print_table", {
            "item": "TOTAL",
            "thaan": int(total_thaan),
            "meter": flt(total_meter, 3),
            "rate": None,
            "amount": flt(total_amount, 2),
        })

    # ---------------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------------

    def _dedupe_child_links(self, childfield: str, linkfield: str):
        """Remove duplicate link rows in a child table (keep first occurrence)."""
        rows = getattr(self, childfield, None) or []
        seen, cleaned, changed = set(), [], False
        for r in rows:
            name = (getattr(r, linkfield, "") or "").strip()
            if not name:
                continue
            if name in seen:
                changed = True
                continue
            seen.add(name)
            cleaned.append(name)
        if changed:
            self.set(childfield, [])
            for name in cleaned:
                self.append(childfield, {linkfield: name})

    # ---------------------------------------------------------------------
    # Part 1: Stock Entries
    # ---------------------------------------------------------------------

    def _aggregate_from_stock_entries(self):
        """
        Each Stock Entry counted ONCE even if duplicated in child table.
        thaan = occurrence count per item across SE lines
        meter = sum(qty) per item across SE lines
        """
        se_names, seen = [], set()
        for r in (self.stock_entry or []):
            se = (r.stock_entry or "").strip()
            if se and se not in seen:
                seen.add(se)
                se_names.append(se)

        agg = {}
        for se_name in se_names:
            try:
                se = frappe.get_doc("Stock Entry", se_name)
            except frappe.DoesNotExistError:
                continue
            for d in (se.items or []):
                item_code = getattr(d, "item_code", None)
                if not item_code:
                    continue
                qty = flt(getattr(d, "qty", 0))
                if qty <= 0:
                    continue
                bucket = agg.setdefault(item_code, {"thaan": 0, "meter": 0.0})
                bucket["thaan"] += 1
                bucket["meter"] += qty
        return agg

    # ---------------------------------------------------------------------
    # Part 2: Case Detail Transfers
    # ---------------------------------------------------------------------

    def _aggregate_from_case_details(self):
        """
        Unique Case Details across all selected transfers.
        For each Case Detail:
          item  = bundle_type (Link -> Item)
          thaan = number of rows in 'items' table
          meter = total_qty
        Group by bundle_type and sum thaan/meter.
        """
        transfer_names = [
            (r.case_detail_transfer or "").strip()
            for r in (self.case_details_transfer or [])
            if r.case_detail_transfer
        ]

        unique_case_details, seen_cases = [], set()
        for tname in transfer_names:
            try:
                cdt = frappe.get_doc("Case Detail Transfer", tname)
            except frappe.DoesNotExistError:
                continue
            for row in (cdt.items or []):
                case_name = (getattr(row, "case_detail", "") or "").strip()
                if case_name and case_name not in seen_cases:
                    seen_cases.add(case_name)
                    unique_case_details.append(case_name)

        agg = {}
        for case_name in unique_case_details:
            try:
                case_doc = frappe.get_doc("Case Detail", case_name)
            except frappe.DoesNotExistError:
                continue

            bundle_type = (getattr(case_doc, "bundle_type", "") or "").strip()
            if not bundle_type:
                continue

            line_count = int(len(getattr(case_doc, "items", []) or []))
            total_qty = flt(getattr(case_doc, "total_qty", 0.0))

            bucket = agg.setdefault(bundle_type, {"thaan": 0, "meter": 0.0})
            bucket["thaan"] += line_count
            bucket["meter"] += total_qty

        return agg
