from frappe.model.document import Document
import frappe
from collections import defaultdict

class RoadChallan(Document):

    def before_save(self):
        """ Auto-populate item-wise details and ensure HSN-wise summary is updated """
        self.clear_items_table()
        self.populate_items_from_case_details()
        self.populate_items_from_delivery_notes()
        self.populate_items_from_stock_entries()
        self.clear_hsn_wise_details()
        self.update_hsn_wise_details()
        self.update_total_cases()  # New function to count unique cases

    def clear_items_table(self):
        """ Clear existing Road Challan Item Wise Details before populating """
        self.road_challan_item_wise_details = []

    def populate_items_from_case_details(self):
        """ Fetch items from all Case Details linked in the Road Challan Case Detail table """
        if not self.case_details:
            return
        
        existing_cases = set()

        for case_row in self.case_details:
            case_detail = case_row.case_detail
            case_no = case_detail  # Use full Case Detail name

            case_detail_doc = frappe.get_doc("Case Detail", case_detail)

            total_qty = case_detail_doc.total_qty or 1  # Avoid division by zero
            total_amount = case_detail_doc.total_amount or 0
            calculated_rate = max(total_amount / total_qty, 200)  # Minimum rate 200

            for item in case_detail_doc.items:
                item_hsn = frappe.db.get_value("Item", item.item_code, "gst_hsn_code") or ""
                rate = calculated_rate  
                value = item.qty * rate  

                self.append("road_challan_item_wise_details", {
                    "item_name": item.item_code,
                    "case_no": case_no,
                    "hsnsac": item_hsn,
                    "qty": item.qty,
                    "uom": item.uom,
                    "rate": rate,
                    "value": value,
                    "remarks": case_row.remarks or ""
                })

                existing_cases.add(case_no)

    def populate_items_from_delivery_notes(self):
        """ Fetch items from all linked Delivery Notes and populate the Road Challan Item Wise Details table """
        if not self.delivery_notes:
            return
        
        existing_cases = set()

        for dn_row in self.delivery_notes:
            delivery_note = dn_row.delivery_note
            case_no = delivery_note[-6:]  

            remarks = dn_row.remarks if hasattr(dn_row, 'remarks') and dn_row.remarks else ""

            delivery_note_doc = frappe.get_doc("Delivery Note", delivery_note)

            for item in delivery_note_doc.items:
                item_hsn = item.gst_hsn_code or frappe.db.get_value("Item", item.item_code, "gst_hsn_code") or ""
                rate = max(item.rate or 0, 200)  
                value = item.qty * rate  

                self.append("road_challan_item_wise_details", {
                    "item_name": item.item_code,
                    "case_no": case_no,
                    "hsnsac": item_hsn,
                    "qty": item.qty,
                    "uom": item.uom,
                    "rate": rate,
                    "value": value,
                    "remarks": remarks  
                })

                existing_cases.add(case_no)

    def populate_items_from_stock_entries(self):
        """ Fetch items from all linked Stock Entries and populate the Road Challan Item Wise Details table """
        if not self.stock_entries:
            return

        existing_cases = set()

        for se_row in self.stock_entries:
            stock_entry = se_row.stock_entry
            case_no = stock_entry[-6:]  

            remarks = se_row.remarks if hasattr(se_row, 'remarks') and se_row.remarks else ""

            stock_entry_doc = frappe.get_doc("Stock Entry", stock_entry)

            for item in stock_entry_doc.items:
                item_hsn = frappe.db.get_value("Item", item.item_code, "gst_hsn_code") or ""
                rate = max((item.basic_rate or 0) * 1.5, 200)  
                value = item.qty * rate  

                self.append("road_challan_item_wise_details", {
                    "item_name": item.item_code,
                    "case_no": case_no,
                    "hsnsac": item_hsn,
                    "qty": item.qty,
                    "uom": item.uom,
                    "rate": rate,  
                    "value": value,  
                    "remarks": remarks  
                })

                existing_cases.add(case_no)

    def clear_hsn_wise_details(self):
        """ Clear existing Road Challan HSN Wise Details before populating """
        self.road_challan_hsn_wise_details = []

    def update_hsn_wise_details(self):
        """ Summarize total quantity & value per HSN from road_challan_item_wise_details """

        if not self.road_challan_item_wise_details:
            return

        hsn_summary = defaultdict(lambda: {"quantity": 0, "value": 0, "uom": None})

        for item in self.road_challan_item_wise_details:
            hsn_code = item.hsnsac or "Unknown"
            uom = item.uom or "Unknown"

            hsn_summary[(hsn_code, uom)]["quantity"] += item.qty
            hsn_summary[(hsn_code, uom)]["value"] += item.value
            hsn_summary[(hsn_code, uom)]["uom"] = uom  

        for (hsn, uom), data in hsn_summary.items():
            self.append("road_challan_hsn_wise_details", {
                "hsn": hsn,
                "quantity": data["quantity"],
                "uom": uom,
                "value": data["value"]
            })

    def update_total_cases(self):
        """ Count unique cases and update the total_cases field """
        unique_cases = set()

        # Collect cases from case_details table
        for row in self.case_details:
            unique_cases.add(row.case_detail)

        # Collect cases from road_challan_item_wise_details table
        for item in self.road_challan_item_wise_details:
            unique_cases.add(item.case_no)

        self.total_cases = len(unique_cases)
