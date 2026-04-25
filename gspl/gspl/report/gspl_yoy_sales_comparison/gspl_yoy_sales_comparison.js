frappe.query_reports["GSPL YoY Sales Comparison"] = {
    "filters": [
        {
            fieldname: "group_by",
            label: "Group By",
            fieldtype: "Select",
            options: [
                "Customer",
                "Item",
                "Item Template",
                "Item Group",
                "Brand",
                "Sales Partner",
                "Customer Group",
                "Territory",
                "Sales Manager",
                "Grade",
                "Content",
                "Region",
                "Division",
                "Area",
            ],
            default: "Customer",
            reqd: 1
        },
        {
            fieldname: "metric",
            label: "Metric",
            fieldtype: "Select",
            options: ["Amount", "Qty"],
            default: "Amount"
        },
        {
            fieldname: "periodicity",
            label: "Periodicity",
            fieldtype: "Select",
            options: ["Monthly", "Quarterly", "Half-Yearly", "Yearly"],
            default: "Monthly"
        },
        {
            fieldname: "from_date",
            label: "From Date",
            fieldtype: "Date",
            default: frappe.datetime.add_months(frappe.datetime.get_today(), -12),
            reqd: 1
        },
        {
            fieldname: "to_date",
            label: "To Date",
            fieldtype: "Date",
            default: frappe.datetime.get_today(),
            reqd: 1
        },
        // Customer filters
        {
            fieldname: "customer",
            label: "Customer",
            fieldtype: "Link",
            options: "Customer"
        },
        {
            fieldname: "sales_partner",
            label: "Sales Partner",
            fieldtype: "Link",
            options: "Sales Partner"
        },
        {
            fieldname: "customer_group",
            label: "Customer Group",
            fieldtype: "Link",
            options: "Customer Group"
        },
        {
            fieldname: "territory",
            label: "Territory",
            fieldtype: "Link",
            options: "Territory"
        },
        {
            fieldname: "sales_manager",
            label: "Sales Manager",
            fieldtype: "Link",
            options: "Sales Person"
        },
        {
            fieldname: "grade",
            label: "Grade",
            fieldtype: "Select",
            options: ["", "A", "Others"]
        },
        // Item filters
        {
            fieldname: "item",
            label: "Item",
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "item_group",
            label: "Item Group",
            fieldtype: "Link",
            options: "Item Group"
        },
        {
            fieldname: "brand",
            label: "Brand",
            fieldtype: "Link",
            options: "Brand"
        },
        {
            fieldname: "variant_of",
            label: "Item Template",
            fieldtype: "Link",
            options: "Item"
        },
        {
            fieldname: "content",
            label: "Content",
            fieldtype: "Select",
            options: ["", "Short Length", "Thaan", "Combi"]
        },
        {
            fieldname: "region",
            label: "Region",
            fieldtype: "Data"
        },
        {
            fieldname: "division",
            label: "Division",
            fieldtype: "Data"
        },
        {
            fieldname: "area",
            label: "Area",
            fieldtype: "Data"
        }
              
    ]
};
