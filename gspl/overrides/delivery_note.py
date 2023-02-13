
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import cint
from erpnext.stock.doctype.batch.batch import get_batch_qty
from frappe.utils import cint, flt

from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

from frappe.utils import logger

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)

class UnableToSelectBatchError(frappe.ValidationError):
	pass


class CustomDeliveryNote(DeliveryNote):
    """
    Overrided DeliveryNote DocType
    """

    #  Trying to override get_batch_no. Futile attempt since this method is called from queries and other places and is difficult to overrite. 

    # def custom_get_batch_no(self, item_code, warehouse, qty=1, throw=False, serial_no=None):
    #     """Do not return any batch number"""
    #     batch_no = None
    #     #batches = get_batches(item_code, warehouse, qty, throw, serial_no)

    #     #for batch in batches:
    #     #    if flt(qty) <= flt(batch.qty):
    #     #       batch_no = batch.batch_id
    #     #       break
        
    #     if not batch_no:
    #         frappe.msgprint(
    #             _(
    #                 "Item {0} did not have a batch. It has been removed."
    #                 ).format(frappe.bold(item_code))
    #         )
    #         if throw:
    #             raise UnableToSelectBatchError
            
                
    #     return batch_no


    # def custom_set_batch_nos(self,warehouse_field, throw=False, child_table="items"):
    #     """Automatically select `batch_no` for outgoing items in item table"""
    #     logger.debug("SEARCH ME HERE")
    #     logger.debug(child_table)
    #     logger.debug(self.get(child_table))
    #     for d in self.get(child_table):
    #         qty = d.get("stock_qty") or d.get("transfer_qty") or d.get("qty") or 0
    #         warehouse = d.get(warehouse_field, None)
    #         if warehouse and qty > 0 and frappe.db.get_value("Item", d.item_code, "has_batch_no"):
    #             if not d.batch_no:
    #                 frappe.msgprint(
    #                     _(
    #                         "Please select a Batch for Item {0}."
    #                         ).format(frappe.bold(item_code))
    #                 )
    #                 raise UnableToSelectBatchError
    #             else:
    #                 batch_qty = custom_get_batch_qty(batch_no=d.batch_no, warehouse=warehouse)
    #                 if flt(batch_qty, d.precision("qty")) != flt(qty, d.precision("qty")):
    #                     frappe.throw(
    #                         _(
    #                         "Row #{0}: The batch {1} has only {2} qty. Please select another batch which has {3} qty available or split the row into multiple rows, to deliver/issue from multiple batches"
    #                     ).format(d.idx, d.batch_no, batch_qty, qty)
    #                     )
                            
    

    def validate(self):
        self.validate_posting_time()
        super(DeliveryNote, self).validate()
        self.set_status()
        self.so_required()
        self.validate_proj_cust()
        self.check_sales_order_on_hold_or_close("against_sales_order")
        self.validate_warehouse()
        self.validate_uom_is_integer("stock_uom", "stock_qty")
        self.validate_uom_is_integer("uom", "qty")
        self.validate_with_previous_doc()
        
        from erpnext.stock.doctype.packed_item.packed_item import make_packing_list
        make_packing_list(self)
        
        # if self._action != "submit" and not self.is_return:
        #     set_batch_nos(self, "warehouse", throw=True)
        #     set_batch_nos(self, "warehouse", throw=True, child_table="packed_items")
        # 
        
        self.update_current_stock()
        
        if not self.installation_status:
            self.installation_status = "Not Installed"
        self.reset_default_field_value("set_warehouse", "items", "warehouse")