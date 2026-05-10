frappe.listview_settings['Batch'] = frappe.listview_settings['Batch'] || {};

// Save the original indicator function so we don't break standard ERPNext logic
const standard_indicator = frappe.listview_settings['Batch'].get_indicator;

frappe.listview_settings['Batch'].get_indicator = function(doc) {
    // 1. Check your new Custom Lock first
    if (doc.custom_locked_by_case_detail) {
        return [__("Locked by Case"), "red", "custom_locked_by_case_detail,=,1"];
    }
    
    // 2. Fall back to standard ERPNext indicators (Expired, Disabled, etc.)
    if (standard_indicator) {
        return standard_indicator(doc);
    }
    
    // 3. Default active state
    return [__("Active"), "green", "disabled,=,0"];
};