from frappe import _


def get_data():
    return {
        "fieldname": "case_detail",
        "transactions": [
            {
                "label": _("Reference"),
                "items": [
                    "Delivery Note",
                    "Sales Invoice",
                ]
            }
        ] 
    }
