from __future__ import unicode_literals
import frappe
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content

# Correct Google Sheet URL (must end in ?gid=xxx)
POSTAL_DATA_URL = "https://docs.google.com/spreadsheets/d/1impXmr318V9v2tSIfLOS9Qtd7nv6qaXTsaE42TJKeB0/edit?gid=366255740"

OFFICE_PRIORITY = {
    "Delivery": 1,
    "H.O": 2,
    "S.O": 3,
    "B.O": 4
}

@frappe.whitelist()
def before_save(doc, method):
    update_customer(doc)

def update_customer(doc):
    for dl in doc.links:
        if dl.link_doctype != "Customer":
            continue

        customer = frappe.get_doc(dl.link_doctype, dl.link_name)

        # GST fields
        if doc.gstin:
            customer.gst_category = "Registered Regular"
            customer.territory = doc.gst_state
            customer.tax_category = "In-State" if doc.gst_state == "West Bengal" else "Out-State"

        # Only update if this is preferred shipping address
        if doc.is_primary_address and doc.pincode:
            try:
                if not frappe.local.flags.get("cached_postal_rows"):
                    content = get_csv_content_from_google_sheets(POSTAL_DATA_URL)
                    rows = read_csv_content(content)
                    frappe.local.flags.cached_postal_rows = rows
                else:
                    rows = frappe.local.flags.cached_postal_rows

                headers = rows[0]
                best_match = None
                best_priority = 999

                for r in rows[1:]:
                    row = dict(zip(headers, r))
                    if row.get("pincode") != str(doc.pincode):
                        continue

                    office_type = "Delivery" if row.get("delivery") == "Delivery" else row.get("officetype")
                    priority = OFFICE_PRIORITY.get(office_type, 999)

                    if priority < best_priority:
                        best_priority = priority
                        best_match = row

                if best_match:
                    customer.region = best_match.get("regionname")
                    customer.division = best_match.get("divisionname")
                    customer.area = best_match.get("officename")

            except Exception:
                frappe.log_error(frappe.get_traceback(), "Address Postal Lookup Failed")

        customer.save()
