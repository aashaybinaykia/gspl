
from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.model.naming import parse_naming_series
from frappe.utils import cint, flt

from erpnext.stock.doctype.batch.batch import get_batch_qty
from erpnext.stock.doctype.delivery_note.delivery_note import DeliveryNote

from erpnext.stock.doctype.batch.batch import get_batch_qty

from frappe.utils import logger
import json

frappe.utils.logger.set_log_level("DEBUG")
logger = frappe.logger("api", allow_site=True, file_count=50)


import qztray
from qztray import QzTray, QzTrayError

@frappe.whitelist()
def get_printer_options():
  try:
    # Create QzTray instance
    qz = QzTray()

    # Fetch list of available printers
    printers = [p['name'] for p in qz.get_printers()]

    return printers

  except QzTrayError as e:
    # handle any errors here
    frappe.throw(str(e))


import qztray
from qztray import QzTray, QzTrayError


@frappe.whitelist()
def print_labels(docname,doctype,printer):
  doc = frappe.get_doc('Item', docname)
  for item in doc.items:
    zpl = """^XA
    ^PW320
    ^FO10,0^BY1,2^BCN,50,N,N^FD{0}^FS
    ^FO5,55^A0N,24,24^FD{0}^FS
    ^FO5,80^A0N,24,24^FD{1}^FS
    ^FO170,105^A0N,24,24^FD{2}^FS
    ^XZ""".format(item.name, item.item_name, item.batch_qty)

    try:
      # Create print job
      qz = QzTray()
      config = qz.get_printer(item.printer_name)
      print_job = config.print_raw(zpl.encode())

      # Send print job to QZ Tray
      qz.send(print_job)

    except QzTrayError as e:
      # handle any errors here
      print(e)