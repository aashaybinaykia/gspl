# Copyright (c) 2023, GSPL and contributors
# For license information, please see license.txt

# import frappe
from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe import _
from frappe.utils.csvutils import get_csv_content_from_google_sheets, read_csv_content

from frappe.utils import logger
from frappe.model.document import Document

import re




class PrintLetters(Document):
	@frappe.whitelist()
	def before_validate(doc):
		doc.contents_html = doc.whatsapp_to_html(doc.contents)

	def whatsapp_to_html(doc,message):
		# Replace underscores with <i> tags for italic
		message = re.sub(r"_([^_]+)_", r"<i>\1</i>", message)
		
		# Replace asterisks with <b> tags for bold
		message = re.sub(r"\*([^\*]+)\*", r"<b>\1</b>", message)
		
		# Replace tildes with <strike> tags for strikethrough
		message = re.sub(r"~([^~]+)~", r"<strike>\1</strike>", message)
		
		# Replace triple backticks with <code> tags for monospace
		message = re.sub(r"```([^`]+)```", r"<code>\1</code>", message)
		
		# Add <br> tags for line breaks
		message = message.replace('\n', '<br>')
		
		# Return the converted message as HTML
		return message
